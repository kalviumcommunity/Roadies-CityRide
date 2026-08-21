# Final Report — Roadies-CityRide

## Business Problem

Roadies-CityRide operates a ride-sharing service across 6 Indian cities. The project investigates:

> **Which city-level behaviours consistently degrade rider experience during high-demand periods?**

## Dataset

- **Source**: Synthetic data generated via `scripts/generate_dataset.py`
- **Grain**: One row per ride request
- **Size**: 50,000 rides (configurable)
- **Cities**: Mumbai, Delhi, Bangalore, Hyderabad, Chennai, Pune
- **Date Range**: 90 days (July–September 2025)
- **Fields**: 20 raw fields including timestamps, city, status, pricing, ratings

## Data Quality

The quality layer includes:
- **Validation**: Schema, type, range, and business rule checks
- **Standardization**: Column naming, type casting, unit normalization
- **Deduplication**: Duplicate detection and removal
- **Consistency**: Cross-field validation and constraint checks
- **Missing Values**: Detection, analysis, and imputation strategies
- **Outlier Detection**: Statistical outlier identification
- **String Cleaning**: Text normalization and validation
- **Datetime Transform**: Timestamp parsing and validation

## Feature Engineering

### Demand/Supply
- `demand_supply_ratio`: Demand vs supply pressure
- `demand_category`: Normal/High/Critical classification

### Surge
- `surge_multiplier`: Price surge factor
- `surge_category`: Low/Medium/High/Extreme classification

### Acceptance
- `was_accepted`: Driver acceptance flag
- `acceptance_rate`: City-level acceptance metrics

### Cancellation
- `rider_cancelled`: Rider cancellation flag
- `driver_cancelled`: Driver cancellation flag
- `cancel_reason`: Categorised cancellation reasons

### Experience
- `wait_time_minutes`: Rider wait time
- `ride_duration_minutes`: Ride duration
- `rating`: Rider rating

### High Demand
- `is_high_demand`: Boolean high-demand flag
- `high_demand_period`: Period classification

## Analysis

### City Segmentation
- K-means clustering of cities by operational metrics
- Behavioral segmentation of riders and drivers

### Time Series
- Hourly and daily operational patterns
- Rolling metrics for trend detection

### Relationships
- Correlation analysis between metrics
- Statistical significance testing

### Distributions
- Metric distribution analysis
- Percentile and quantile calculations

### Funnel Analysis
- Ride request → acceptance → completion funnel
- Drop-off point identification

### Root Cause Analysis
- City degradation identification
- Operational chain tracing

### Anomaly Detection
- Statistical anomaly identification
- Risk classification

### NumPy Workflow
- Vectorized computation benchmarks (15-17x speedup)

## SQL Analytics

- **Database**: SQLite at `data/roadies.db`
- **Schemas**: `sql/schemas/rides.sql`
- **Business Metrics**: `sql/queries/business_metrics.sql`
- **Advanced Analysis**: `sql/queries/advanced_analysis.sql`
- **Views**: `sql/views/analytics_views.sql` (4 views, 2 aggregation tables)
- **Validation**: Python/SQL metric comparison with drift detection

## Dashboard

### Pages
1. **Overview**: Core KPIs, high-demand impact, city summary
2. **City Analysis**: Compare cities, heatmap, metric selection
3. **High-Demand Analysis**: Normal vs high demand, deterioration
4. **Risk & Anomalies**: Anomaly detection, risk ranking

### Filters
- Cities (multi-select)
- Demand Period (All/Normal/High)
- Surge Range (slider)

## Monitoring

### Pipeline Stages
1. Load dataset
2. Feature engineering
3. KPI calculation
4. Alert evaluation

### Alert Rules
| Alert | Threshold | Severity |
|---|---|---|
| Rider cancel > 20% | HIGH |
| Acceptance < 70% | CRITICAL |
| Wait time > 15 min | HIGH |
| Surge > 2.0x | HIGH |
| City variants | Per city |

## Key Business Findings

1. **Acceptance deterioration**: All cities show reduced driver acceptance during high-demand periods
2. **Cancellation increase**: Rider cancellations rise significantly during high demand
3. **Wait time increase**: Average wait times increase across all cities
4. **Surge pressure**: Surge pricing correlates with demand/supply imbalance
5. **City variation**: Chennai and Mumbai show the most severe degradation
6. **Temporal patterns**: Evening hours (6-9 PM) show peak deterioration

## Limitations

1. **Synthetic data**: Generated dataset, not real operational data
2. **Threshold-dependent**: Alert classifications depend on configured thresholds
3. **Not causal**: Anomaly detection identifies patterns, not causes
4. **Rule-based segmentation**: Uses predefined rules, not ML clustering
5. **Analytical conclusions**: Depend on generated data characteristics

## Test Results

- **Total**: 573 tests
- **Passed**: 548
- **Skipped**: 25 (missing generated dataset)
- **Failed**: 0

## Reproducibility

A fresh developer can reproduce the full workflow:

```bash
git clone https://github.com/kalviumcommunity/Roadies-CityRide.git
cd Roadies-CityRide
uv sync
uv run python scripts/generate_dataset.py --rows 50000 --seed 42
uv run pytest
uv run python scripts/run_pipeline.py
uv run streamlit run dashboard/app.py
```
