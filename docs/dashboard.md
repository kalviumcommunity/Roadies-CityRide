# Dashboard — Roadies-CityRide

## Overview

Interactive Streamlit dashboard for exploring ride-sharing rider experience analytics.

## Running the Dashboard

```bash
uv run streamlit run dashboard/app.py
```

## Pages

| Page | File | Description |
|---|---|---|
| Overview | `pages/1_overview.py` | Core KPIs, high-demand impact, city summary |
| City Analysis | `pages/2_city_analysis.py` | Compare cities, heatmap, metric selection |
| High-Demand | `pages/3_high_demand.py` | Normal vs high demand, deterioration |
| Risk & Anomalies | `pages/4_risk_anomalies.py` | Anomaly detection, risk ranking |

## Filters

- **Cities**: Multi-select to filter by city
- **Demand Period**: All / Normal / High
- **Surge Range**: Slider for surge multiplier range

## Data Source

Loads data from `data/raw/rides.csv` via the existing ingestion layer.

Feature engineering is applied on load using:
- `demand_supply`
- `surge`
- `acceptance`
- `cancellation`
- `experience`
- `demand_period`

## Components Used

| Component | Source |
|---|---|
| KPIs | `roadies.visualization.kpis` |
| Charts | `roadies.visualization` |
| Anomalies | `roadies.analysis.anomaly` |
| Features | `roadies.features.*` |
