# Roadies-CityRide Architecture

> This document explains the project structure, what each directory is responsible for, and how it maps to the 50-assignment roadmap.

## Project Overview

Roadies-CityRide is an analytics data product that answers:

**Which city-level behaviours consistently degrade rider experience during high-demand periods?**

The project processes synthetic ride-sharing data through ingestion, cleaning, feature engineering, analysis, SQL analytics, visualisation, and a Streamlit dashboard.

## Directory Structure

```
Roadies-CityRide/
├── README.md                  # Project overview and quick start
├── pyproject.toml             # Python project config (Issue #7)
├── uv.lock                    # Locked dependencies (Issue #7)
├── .gitignore                 # Git ignore rules
│
├── docs/                      # All documentation
│   ├── assignments.md         # 50-assignment tracker
│   ├── architecture.md        # This file
│   ├── prd.md                 # Product requirements (Issue #1)
│   ├── business_questions.md  # Business questions (Issue #2)
│   ├── kpi_definitions.md     # KPI catalogue (Issue #3)
│   ├── methodology.md         # Analytical methodology (Issue #4)
│   ├── ux_design.md           # Dashboard UX design (Issue #5)
│   ├── data_dictionary.md     # Dataset field definitions (Issue #15)
│   ├── insights.md            # Final findings (Issue #50)
│   └── delivery.md            # Delivery instructions (Issue #50)
│
├── data/                      # All data files
│   ├── raw/                   # Original, unmodified dataset files
│   ├── processed/             # Cleaned and transformed data
│   └── synthetic/             # Generated synthetic datasets
│
├── src/                       # Reusable Python source code
│   └── roadies/               # Main package
│       ├── __init__.py
│       ├── ingestion/         # Data loading and generation (Issues #12-#13)
│       ├── quality/           # Data cleaning and validation (Issues #16-#24)
│       ├── features/          # Feature engineering (Issues #25-#30)
│       ├── analysis/          # Python analysis and NumPy (Issues #31-#40)
│       ├── database/          # SQL integration (Issues #41-#45)
│       ├── visualization/     # Plotly charts (Issues #46-#47)
│       └── pipeline/          # Pipeline orchestration (Issues #10, #49)
│
├── sql/                       # SQL analytics layer
│   ├── schemas/               # Table definitions (Issue #41)
│   ├── queries/               # Business metric queries (Issue #42)
│   ├── views/                 # Aggregation views (Issue #44)
│   └── validations/           # SQL validation queries (Issue #45)
│
├── notebooks/                 # Exploratory analysis notebooks (Issues #31-#40)
│
├── dashboard/                 # Streamlit application
│   ├── app.py                 # Main entry point (Issue #48)
│   └── pages/                 # Individual dashboard pages (Issue #48)
│
├── scripts/                   # CLI entry points and utilities
│   └── run_pipeline.py        # Pipeline runner (Issue #49)
│
└── tests/                     # Test suite
    ├── __init__.py
    ├── test_ingestion.py      # Ingestion tests (Issue #13)
    ├── test_quality.py        # Quality tests (Issues #16-#24)
    ├── test_features.py       # Feature tests (Issues #25-#30)
    └── test_analysis.py       # Analysis tests (Issues #31-#40)
```

## Directory Responsibilities

### `data/`
Where all data files live. Never edit files in `raw/` directly.

| Subdirectory | Purpose | Example Files |
|---|---|---|
| `data/raw/` | Original, unmodified dataset files | `rides.csv`, `drivers.csv` |
| `data/processed/` | Cleaned, validated, transformed data | `rides_clean.parquet` |
| `data/synthetic/` | Generated synthetic datasets | `synthetic_rides.csv` |

### `src/roadies/`
Reusable Python code organised by domain. Each subpackage handles one stage of the data pipeline.

| Subpackage | Purpose | Key Assignments |
|---|---|---|
| `ingestion/` | Load data from files, generate synthetic data | #12, #13 |
| `quality/` | Clean, validate, profile data | #16-#24 |
| `features/` | Engineer derived features | #25-#30 |
| `analysis/` | Python-based statistical analysis | #31-#40 |
| `database/` | SQLite integration, SQL execution | #41-#45 |
| `visualization/` | Plotly chart functions | #46-#47 |
| `pipeline/` | Orchestrate the full pipeline | #10, #49 |

### `sql/`
SQL queries and database objects. All queries target SQLite.

| Subdirectory | Purpose |
|---|---|
| `schemas/` | CREATE TABLE statements |
| `queries/` | Business metric queries |
| `views/` | Reusable aggregation views |
| `validations/` | SQL-based data validation |

### `notebooks/`
Jupyter notebooks for exploratory analysis. These are disposable explorations; reusable logic moves to `src/roadies/`.

### `dashboard/`
Streamlit web application. Entry point is `app.py`; individual pages go in `pages/`.

### `scripts/`
CLI entry points. These import from `src/roadies/` and are run via `uv run python scripts/...`.

### `tests/`
Pytest test suite. Mirrors the `src/roadies/` structure.

## Data Flow

```
data/raw/          (original files)
      ↓
src/roadies/ingestion/     (load into DataFrames)
      ↓
src/roadies/quality/       (clean, validate, profile)
      ↓
data/processed/    (cleaned data)
      ↓
src/roadies/features/      (engineer features)
      ↓
src/roadies/analysis/      (Python analysis)
      ↓
src/roadies/database/      (load into SQLite)
      ↓
sql/queries/       (SQL analytics)
      ↓
src/roadies/visualization/ (Plotly charts)
      ↓
dashboard/         (Streamlit app)
```

## Mapping to the 50-Assignment Roadmap

| Phase | Assignments | Key Directories |
|---|---|---|
| A: Product Definition | #1-#5 | `docs/` |
| B: Project Setup | #6-#10 | Root + `src/` + `scripts/` |
| C: Dataset Creation | #11-#15 | `data/raw/`, `src/roadies/ingestion/`, `docs/` |
| D: Data Quality | #16-#24 | `src/roadies/quality/`, `tests/` |
| E: Feature Engineering | #25-#30 | `src/roadies/features/` |
| F: Python Analysis | #31-#40 | `src/roadies/analysis/`, `notebooks/` |
| G: SQL Analytics | #41-#45 | `src/roadies/database/`, `sql/` |
| H: Visual Product | #46-#48 | `src/roadies/visualization/`, `dashboard/` |
| I: Productionization | #49-#50 | `src/roadies/pipeline/`, `scripts/`, `docs/` |

## Design Decisions

1. **`src/roadies/` not `src/roadies_cityride/`** - Shorter import path (`from roadies.quality import ...`). The distribution name in `pyproject.toml` can still be `roadies-cityride`.

2. **SQLite for SQL layer** - Lightweight, no server required, file-based. Sufficient for a portfolio/analytics project.

3. **Separate `sql/` directory** - SQL lives outside `src/` because SQL files are not Python imports. They are loaded or executed separately.

4. **`notebooks/` for exploration only** - Reusable logic moves to `src/roadies/`. Notebooks are not part of the installed package.

5. **`.gitkeep` files** - Git does not track empty directories. `.gitkeep` files ensure the directory structure is preserved in version control.

6. **No `config/` directory yet** - Configuration management is handled in Issue #8. The structure is ready for it.
