# 📊 SQL Logistics Performance Insights

A comprehensive SQL-based analytics suite for logistics performance tracking. Analyze driver efficiency, route optimization, fuel consumption, and delivery reliability with automated reporting.

## ✨ Features

- 🚗 **Driver Performance Analysis** - Delays, fuel efficiency, on-time rates
- 🗺️ **Route Optimization** - Performance metrics by route
- ⛽ **Fuel Efficiency Tracking** - km/liter calculations and rankings
- ⏱️ **Delivery Delays** - Identify problem deliveries and patterns
- 📈 **Multi-Format Reports** - Automated PDF visualizations & CSV exports

## 🚀 Quick Start

### Prerequisites
- Python 3.8+

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/driver-analytics.git
cd driver-analytics
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

### Run Analytics

```bash
python run_analytics.py
```

**This will:**
- Load delivery data from `deliveries.csv`
- Create SQLite database
- Execute SQL analytics queries
- Generate CSV results in `results/` folder
- Create PDF report with visualizations

## 📁 Output Files

### CSV Reports (`results/` folder)
- `driver_performance_summary.csv` - Overall driver metrics
- `route_performance_summary.csv` - Route-level analysis
- `best_drivers_by_fuel_efficiency.csv` - Top fuel-efficient drivers
- `on_time_rate_by_driver_route.csv` - On-time delivery by driver & route
- `top_delayed_deliveries.csv` - Problem deliveries
- `duration_per_delivery.csv` - Delivery duration breakdown

### PDF Report
- `Driver_Performance_Report_YYYY-MM-DD.pdf` - Executive dashboard with charts

## 🎯 Usage Examples

```bash
# Default run
python run_analytics.py

# Custom data source
python run_analytics.py --csv custom_deliveries.csv

# Custom output location
python run_analytics.py --results ./my_reports

# Custom report name
python run_analytics.py --report-prefix "Weekly_Analysis"

# All options combined
python run_analytics.py --csv data.csv --results ./output --report-prefix "Report"
```

## 📊 SQL Queries Included

1. **Duration per Delivery** - Calculate actual delivery times
2. **Driver Performance Summary** - Aggregate metrics per driver
3. **Route Performance Summary** - Route-level efficiency analysis
4. **Top Delayed Deliveries** - Identify problem areas
5. **Best Drivers by Fuel Efficiency** - Fuel efficiency rankings
6. **On-Time Rate by Driver & Route** - Reliability metrics

**Customize queries:** Edit the `SQL_QUERIES` dictionary in `run_analytics.py`

## 📋 Data Requirements

Your `deliveries.csv` should include:

| Column | Type | Description |
|--------|------|-------------|
| `delivery_id` | int | Unique identifier |
| `driver` | string | Driver name |
| `route` | string | Route code |
| `start_time` | datetime | Delivery start |
| `end_time` | datetime | Delivery end |
| `distance_km` | float | Distance traveled |
| `fuel_liters` | float | Fuel consumed |
| `delay_minutes` | int | Minutes delayed |
| `status` | string | Delivery status |

## 📦 Generated Files

- `transport.db` - SQLite database (auto-generated)
- `results/` - All CSV and PDF outputs

## 🛠️ Customization

### Add New Queries
Edit `run_analytics.py` and add to `SQL_QUERIES` dictionary:

```python
SQL_QUERIES = {
    'your_query_name': """
        SELECT ... FROM deliveries WHERE ...
    """,
    # ... existing queries
}
```

### Modify Report Output
Adjust chart colors, sizes, and styles in the `build_report()` function.

## 📝 Requirements

- Python 3.8+
- pandas >=2.0.0
- matplotlib >=3.7.0

## 📄 License

MIT

## 🤝 Contributing

Contributions welcome! Feel free to fork, modify, and submit improvements.
