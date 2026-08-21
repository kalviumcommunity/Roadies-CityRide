# Roadies-CityRide

A ride-sharing company captures driver acceptance rates, rider cancellation patterns, and surge pricing data, but no operational model explains which city-level behaviours consistently degrade rider experience during high-demand periods.

## Business Problem

Roadies-CityRide operates across 6 cities (Mumbai, Delhi, Bangalore, Hyderabad, Chennai, Pune). The core question is:

> **Which city-level behaviours consistently degrade rider experience during high-demand periods?**

This project builds a complete analytical data product to answer that question.

## Project Structure

```
Roadies-CityRide/
├── data/                  # Dataset files
│   ├── raw/               #   Original, unmodified data
│   ├── processed/         #   Cleaned and transformed data
│   └── synthetic/         #   Generated synthetic datasets
├── src/roadies/           # Reusable Python source code
│   ├── ingestion/         #   Data loading and generation
│   ├── quality/           #   Cleaning and validation
│   ├── features/          #   Feature engineering
│   ├── analysis/          #   Statistical analysis
│   ├── database/          #   SQL integration
│   ├── visualization/     #   Plotly charts
│   ├── monitoring/        #   Pipeline and alerts
│   └── validation/        #   SQL/Python validation
├── sql/                   # SQL queries and views
├── notebooks/             # Exploratory analysis notebooks
├── dashboard/             # Streamlit application
├── scripts/               # CLI entry points
├── tests/                 # Test suite
└── docs/                  # Documentation
```

## Quick Start

**Prerequisites:** Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
# 1. Clone and install
git clone https://github.com/kalviumcommunity/Roadies-CityRide.git
cd Roadies-CityRide
uv sync

# 2. Generate dataset
uv run python scripts/generate_dataset.py --rows 50000 --seed 42

# 3. Run tests
uv run pytest

# 4. Run analytical pipeline
uv run python scripts/run_pipeline.py

# 5. Start dashboard
uv run streamlit run dashboard/app.py
```

## Generate Dataset

```bash
# Default: 50,000 rides
uv run python scripts/generate_dataset.py

# Custom row count and seed
uv run python scripts/generate_dataset.py --rows 10000 --seed 123
```

## Configuration

Copy `.env.example` to `.env` and adjust as needed:

```bash
cp .env.example .env
```

Key variables: `ROADIES_ENVIRONMENT`, `ROADIES_RANDOM_SEED`, `ROADIES_DATABASE_URL`.

## Testing

```bash
# Run full test suite
uv run pytest

# Run specific test file
uv run pytest tests/test_validation.py -v
```

## Dashboard

```bash
uv run streamlit run dashboard/app.py
```

Pages: Overview, City Analysis, High-Demand Analysis, Risk & Anomalies.

## Pipeline

```bash
# Run analytical pipeline with monitoring
uv run python scripts/run_pipeline.py
```

## Documentation

- [Architecture](docs/architecture.md)
- [Data Dictionary](docs/data_dictionary.md)
- [Assignment Tracker](docs/assignments.md)
- [KPI Definitions](docs/kpis.md)
- [Visualisation Guide](docs/visualization.md)
- [Dashboard Guide](docs/dashboard.md)
- [Monitoring Guide](docs/monitoring.md)
- [SQL Setup](docs/sql_setup.md)
- [Final Report](docs/final_report.md)

## Key Findings

- All 6 cities show acceptance deterioration during high-demand periods
- Mumbai and Chennai have the highest cancellation rates during high demand
- Wait times increase significantly across all cities during high demand
- Surge pricing correlates with demand/supply pressure
- Chennai shows the most severe degradation across multiple metrics

## Limitations

- **Synthetic data**: Dataset is generated, not from real operations
- **Threshold-dependent**: Alert classifications depend on configured thresholds
- **Not causal**: Anomaly detection identifies patterns, not causes
- **Rule-based**: Segmentation uses predefined rules, not ML clustering
- **Analytical**: Conclusions depend on generated data characteristics

## Assignment Roadmap

This project follows a 50-assignment roadmap. See [docs/assignments.md](docs/assignments.md) for the full tracker.
