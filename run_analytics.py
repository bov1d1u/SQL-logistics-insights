import argparse
import sqlite3
from pathlib import Path
from datetime import datetime

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import pandas as pd


SQL_QUERIES = {
    'duration_per_delivery': """
SELECT
    delivery_id,
    driver,
    route,
    start_time,
    end_time,
    ROUND((julianday(end_time) - julianday(start_time)) * 1440, 0) AS duration_minutes,
    distance_km,
    fuel_liters,
    delay_minutes,
    status
FROM deliveries;
""",
    'driver_performance_summary': """
SELECT
    driver,
    COUNT(*) AS total_deliveries,
    ROUND(AVG(delay_minutes), 1) AS avg_delay,
    ROUND(SUM(distance_km), 1) AS total_distance_km,
    ROUND(SUM(distance_km) / SUM(fuel_liters), 2) AS fuel_efficiency_km_per_l,
    ROUND(AVG(CASE WHEN delay_minutes = 0 THEN 1.0 ELSE 0.0 END) * 100, 1) AS on_time_percentage
FROM deliveries
GROUP BY driver
ORDER BY on_time_percentage DESC, avg_delay ASC;
""",
    'route_performance_summary': """
SELECT
    route,
    COUNT(*) AS total_deliveries,
    ROUND(AVG(delay_minutes), 1) AS avg_delay,
    ROUND(AVG((julianday(end_time) - julianday(start_time)) * 1440), 0) AS avg_duration_minutes,
    ROUND(AVG(distance_km), 1) AS avg_distance_km,
    ROUND(SUM(distance_km) / SUM(fuel_liters), 2) AS fuel_efficiency_km_per_l,
    ROUND(AVG(CASE WHEN delay_minutes = 0 THEN 1.0 ELSE 0.0 END) * 100, 1) AS on_time_percentage
FROM deliveries
GROUP BY route
ORDER BY avg_delay DESC;
""",
    'top_delayed_deliveries': """
SELECT
    delivery_id,
    driver,
    route,
    delay_minutes,
    status,
    ROUND((julianday(end_time) - julianday(start_time)) * 1440, 0) AS duration_minutes
FROM deliveries
ORDER BY delay_minutes DESC
LIMIT 10;
""",
    'best_drivers_by_fuel_efficiency': """
SELECT
    driver,
    ROUND(SUM(distance_km) / SUM(fuel_liters), 2) AS fuel_efficiency_km_per_l,
    COUNT(*) AS deliveries
FROM deliveries
GROUP BY driver
ORDER BY fuel_efficiency_km_per_l DESC;
""",
    'on_time_rate_by_driver_route': """
SELECT
    driver,
    route,
    COUNT(*) AS deliveries,
    SUM(CASE WHEN delay_minutes = 0 THEN 1 ELSE 0 END) AS on_time_deliveries,
    ROUND(SUM(CASE WHEN delay_minutes = 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS on_time_percentage
FROM deliveries
GROUP BY driver, route
ORDER BY on_time_percentage DESC, deliveries DESC;
""",
}


def build_database(csv_path: Path, db_path: Path) -> sqlite3.Connection:
    df = pd.read_csv(csv_path)
    if 'start_time' in df.columns and 'end_time' in df.columns:
        df[['start_time', 'end_time']] = df[['start_time', 'end_time']].astype(str)
    conn = sqlite3.connect(db_path)
    df.to_sql('deliveries', conn, if_exists='replace', index=False)
    return conn


def export_sql_results(conn: sqlite3.Connection, results_dir: Path) -> None:
    for name, query in SQL_QUERIES.items():
        df = pd.read_sql_query(query, conn)
        path = results_dir / f'{name}.csv'
        df.to_csv(path, index=False)
        print(f'Saved SQL result: {path}')


def build_report(df: pd.DataFrame, results_dir: Path, output_prefix: str) -> None:
    df['start_time'] = pd.to_datetime(df['start_time'])
    df['end_time'] = pd.to_datetime(df['end_time'])
    df['duration_minutes'] = (df['end_time'] - df['start_time']).dt.total_seconds() / 60

    driver_group = df.groupby('driver')
    report = pd.DataFrame({
        'Total Deliveries': driver_group['delivery_id'].count(),
        'Average Delay (min)': driver_group['delay_minutes'].mean().round(2),
        'Total Distance (km)': driver_group['distance_km'].sum(),
        'Fuel Efficiency (km/l)': (driver_group['distance_km'].sum() / driver_group['fuel_liters'].sum()).round(2),
        'On-Time Delivery %': driver_group.apply(lambda x: (x['delay_minutes'] == 0).mean() * 100).round(1)
    })
    report['Score'] = (100 - report['Average Delay (min)']) + report['On-Time Delivery %']

    results_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime('%Y-%m-%d')
    pdf_path = results_dir / f'{output_prefix}_{today}.pdf'
    csv_path = results_dir / f'{output_prefix}_{today}.csv'

    with PdfPages(pdf_path) as pdf:
        fig, ax = plt.subplots(figsize=(11, 8))
        ax.axis('off')
        table = ax.table(
            cellText=report.drop('Score', axis=1).values,
            colLabels=report.drop('Score', axis=1).columns,
            rowLabels=report.index,
            cellLoc='center',
            loc='center'
        )
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 2.5)
        plt.title('Driver Performance Summary Report', fontsize=16, fontweight='bold', pad=20)
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()

        chart_specs = [
            ('Total Deliveries', 'Number of Deliveries', 'steelblue'),
            ('Average Delay (min)', 'Delay (minutes)', 'orange'),
            ('Fuel Efficiency (km/l)', 'km per liter', 'green'),
            ('On-Time Delivery %', 'On-Time %', 'purple'),
        ]
        for col, ylabel, color in chart_specs:
            fig, ax = plt.subplots(figsize=(10, 6))
            report[col].plot(kind='bar', ax=ax, color=color)
            ax.set_title(f'{col} per Driver', fontsize=14, fontweight='bold')
            ax.set_xlabel('Driver')
            ax.set_ylabel(ylabel)
            plt.tight_layout()
            pdf.savefig(fig, bbox_inches='tight')
            plt.close()

        route_summary = df.groupby('route').agg(
            avg_delay=('delay_minutes', 'mean'),
            avg_duration_minutes=('duration_minutes', 'mean'),
            avg_distance_km=('distance_km', 'mean'),
            fuel_efficiency_km_per_l=('distance_km', lambda x: x.sum() / df.loc[x.index, 'fuel_liters'].sum()),
            on_time_percentage=('delay_minutes', lambda x: (x == 0).mean() * 100)
        ).reset_index()
        route_summary['avg_delay'] = route_summary['avg_delay'].round(1)
        route_summary['avg_duration_minutes'] = route_summary['avg_duration_minutes'].round(0)
        route_summary['avg_distance_km'] = route_summary['avg_distance_km'].round(1)
        route_summary['fuel_efficiency_km_per_l'] = route_summary['fuel_efficiency_km_per_l'].round(2)
        route_summary['on_time_percentage'] = route_summary['on_time_percentage'].round(1)

        fig, ax = plt.subplots(figsize=(10, 6))
        route_summary.set_index('route')['avg_delay'].plot(kind='bar', ax=ax, color='darkorange')
        ax.set_title('Average Delay by Route', fontsize=14, fontweight='bold')
        ax.set_xlabel('Route')
        ax.set_ylabel('Average Delay (min)')
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()

        fig, ax = plt.subplots(figsize=(10, 6))
        route_summary.set_index('route')['fuel_efficiency_km_per_l'].plot(kind='bar', ax=ax, color='seagreen')
        ax.set_title('Fuel Efficiency by Route', fontsize=14, fontweight='bold')
        ax.set_xlabel('Route')
        ax.set_ylabel('Fuel Efficiency (km/l)')
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()

        fig, ax = plt.subplots(figsize=(10, 6))
        route_summary.set_index('route')['on_time_percentage'].plot(kind='bar', ax=ax, color='purple')
        ax.set_title('On-Time Delivery Rate by Route', fontsize=14, fontweight='bold')
        ax.set_xlabel('Route')
        ax.set_ylabel('On-Time %')
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()

        top_delayed = df.sort_values('delay_minutes', ascending=False).head(10)
        fig, ax = plt.subplots(figsize=(10, 6))
        top_delayed.plot(kind='bar', x='delivery_id', y='delay_minutes', color='crimson', legend=False, ax=ax)
        ax.set_title('Top Delayed Deliveries', fontsize=14, fontweight='bold')
        ax.set_xlabel('Delivery ID')
        ax.set_ylabel('Delay (min)')
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()

    report.drop('Score', axis=1).to_csv(csv_path)
    print(f'Saved PDF: {pdf_path}')
    print(f'Saved CSV: {csv_path}')


def main() -> None:
    parser = argparse.ArgumentParser(description='Run analytics for the logistics dataset.')
    parser.add_argument('--csv', type=Path, default=Path('deliveries.csv'), help='Path to deliveries CSV file')
    parser.add_argument('--db', type=Path, default=Path('transport.db'), help='SQLite database file path')
    parser.add_argument('--results', type=Path, default=Path('results'), help='Directory to write CSV and PDF results')
    parser.add_argument('--report-prefix', default='Driver_Performance_Report', help='Prefix for the PDF and CSV report names')
    args = parser.parse_args()

    args.results.mkdir(parents=True, exist_ok=True)
    conn = build_database(args.csv, args.db)
    export_sql_results(conn, args.results)
    conn.close()

    df = pd.read_csv(args.csv)
    build_report(df, args.results, args.report_prefix)


if __name__ == '__main__':
    main()
