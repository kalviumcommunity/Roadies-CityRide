# SQL Advanced Analysis — Roadies-CityRide

## Overview

This document describes the advanced SQL analysis using joins, window functions, and analytical queries.

## Joins Implemented

| Join | Purpose | Tables |
|---|---|---|
| city_normal JOIN city_high | Compare normal vs high demand by city | CTEs |
| city_contributions CROSS JOIN totals | Calculate city share of total | CTEs |
| city_metrics CROSS JOIN global_avg | Compare city vs global average | CTEs |

## Window Functions

| Function | Purpose | Partition | Order |
|---|---|---|---|
| RANK() | Rank cities by cancellation | None | cancel_rate DESC |
| RANK() | Rank cities by deterioration | None | deterioration DESC |
| SUM() OVER | Running total of rides | None | ride_date |
| AVG() OVER | 7-day moving average | None | ride_date |
| PERCENT_RANK() | Percentile ranking | None | deterioration |

## Advanced Queries

### city_cancel_ranking
- **Purpose**: Rank cities by high-demand rider cancellation rate
- **Grain**: One row per city
- **Key columns**: city, cancel_rate, cancel_rank

### city_deterioration_ranking
- **Purpose**: Rank cities by acceptance deterioration during high demand
- **Grain**: One row per city
- **Key columns**: city, normal_acceptance, high_acceptance, deterioration

### within_city_baseline
- **Purpose**: Compare each city's high-demand metrics against its own normal baseline
- **Grain**: One row per city
- **Key columns**: city, normal_wait, high_wait, wait_change, cancel_change

### running_metrics
- **Purpose**: Daily ride volume with running total and 7-day moving average
- **Grain**: One row per day
- **Key columns**: ride_date, daily_rides, running_total, moving_avg_7day

### city_contribution
- **Purpose**: Each city's contribution to total rides and cancellations
- **Grain**: One row per city
- **Key columns**: city, ride_share_pct, cancel_share_pct

### city_deviation
- **Purpose**: How each city compares to the overall average
- **Grain**: One row per city
- **Key columns**: city, wait_vs_avg, surge_vs_avg, cancel_vs_avg

## Query Execution

```python
from roadies.database import execute_advanced_query

# Get city cancellation ranking
ranking = execute_advanced_query("city_cancel_ranking")

# Get within-city baseline comparison
baseline = execute_advanced_query("within_city_baseline")

# Get running metrics
running = execute_advanced_query("running_metrics")
```
