# SQL Optimization and Views — Roadies-CityRide

## Overview

This document describes the SQL query optimization and reusable views created for the analytical layer.

## Views Created

| View | Grain | Purpose |
|---|---|---|
| vw_city_performance | One row per city | Core city-level metrics |
| vw_city_demand_comparison | One row per city per demand period | Normal vs high demand |
| vw_city_deterioration | One row per city | Quantify deterioration |
| vw_rider_experience | One row per city | Rider-facing metrics |

## Aggregation Tables

| Table | Grain | Purpose | updated_at |
|---|---|---|---|
| agg_daily_metrics | One row per day | Daily trend analysis | Yes |
| agg_city_metrics | One row per city | Fast city-level queries | Yes |

## Optimization Techniques

### 1. Explicit Column Selection
- Replaced `SELECT *` with specific columns
- Reduced data transfer and memory usage

### 2. Early Filtering
- Added `WHERE` clauses before aggregation
- Reduced rows processed

### 3. CTE Reuse
- Common table expressions for repeated logic
- Improved readability and maintainability

### 4. Pre-aggregation
- Materialized expensive aggregations
- Reduced repeated computation

## Query Execution

```python
from roadies.database import create_views, query_view

# Create views
create_views()

# Query views
city_perf = query_view("vw_city_performance")
demand_comp = query_view("vw_city_demand_comparison", where="city = 'Mumbai'")

# Query aggregation tables
daily = query("SELECT * FROM agg_daily_metrics ORDER BY ride_date DESC")
```

## Result Validation

All views produce identical results to their direct query equivalents:
- City performance view matches city_metrics query
- Deterioration view matches city_deterioration query

## Refresh Expectations

- **Views**: Always reflect current data (no refresh needed)
- **Aggregation tables**: Refresh by re-running INSERT statements
- **updated_at**: Indicates when aggregation was last refreshed
