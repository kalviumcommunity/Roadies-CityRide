# SQL Business Metrics — Roadies-CityRide

## Overview

This document describes the SQL business metrics implemented for the Roadies-CityRide analytical database.

## Core Metrics

| Metric | SQL Expression | Description |
|---|---|---|
| total_rides | COUNT(*) | Total ride requests |
| accepted_rides | SUM(was_accepted) | Rides accepted by drivers |
| completed_rides | SUM(ride_completed) | Successfully completed rides |
| rider_cancellations | SUM(rider_cancelled) | Cancellations by riders |
| driver_cancellations | SUM(driver_cancelled) | Cancellations by drivers |
| acceptance_rate | SUM(was_accepted) / COUNT(*) * 100 | % of requests accepted |
| completion_rate | SUM(ride_completed) / COUNT(*) * 100 | % of requests completed |
| rider_cancel_rate | SUM(rider_cancelled) / COUNT(*) * 100 | % cancelled by riders |
| driver_cancel_rate | SUM(driver_cancelled) / COUNT(*) * 100 | % cancelled by drivers |
| avg_wait_time | AVG(wait_time_minutes) | Average wait time |
| avg_surge | AVG(surge_multiplier) | Average surge multiplier |
| avg_demand_supply_ratio | AVG(demand_supply_ratio) | Average demand/supply ratio |
| high_demand_share | SUM(is_high_demand) / COUNT(*) * 100 | % of high-demand rides |

## City-Level Metrics

Same metrics as core, grouped by `city`.

## Demand Comparison

Metrics split by `is_high_demand` (0=normal, 1=high).

## Time-Based Metrics

- **Daily**: Metrics by date
- **Hourly**: Metrics by hour of day
- **Day of week**: Metrics by day name

## City Deterioration

Compares normal vs high-demand for each city:
- `normal_*`: Metric value during normal demand
- `high_*`: Metric value during high demand
- `*_change`: Difference (high - normal)

## Query Execution

```python
from roadies.database import execute_metric_query

# Get core metrics
core = execute_metric_query("core_metrics")

# Get city metrics
city = execute_metric_query("city_metrics")

# Get demand comparison
demand = execute_metric_query("demand_comparison")
```

## Available Queries

| Query Name | Description |
|---|---|
| core_metrics | Global business metrics |
| city_metrics | Metrics by city |
| demand_comparison | Normal vs high demand |
| daily_metrics | Metrics by date |
| hourly_metrics | Metrics by hour |
| city_deterioration | City-level deterioration |
