# Roadies-CityRide

A ride-sharing company captures driver acceptance rates, rider cancellation patterns, and surge pricing data, but no operational model explains which city-level behaviours consistently degrade rider experience during high-demand periods.

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
│   └── pipeline/          #   Pipeline orchestration
├── sql/                   # SQL queries and views
├── notebooks/             # Exploratory analysis notebooks
├── dashboard/             # Streamlit application
├── scripts/               # CLI entry points
├── tests/                 # Test suite
└── docs/                  # Documentation
```

For a detailed explanation of each directory and how it maps to the assignment roadmap, see [docs/architecture.md](docs/architecture.md).

## Assignment Roadmap

This project follows a 50-assignment roadmap. See [docs/assignments.md](docs/assignments.md) for the full tracker.
