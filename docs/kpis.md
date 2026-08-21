# KPI Cards and Summary Metrics — Roadies-CityRide

## Overview

Reusable KPI calculation, comparison, and formatting for the ride-sharing dashboard.

## KPI Set

### Core Operational KPIs

| KPI | Formula | Unit | Higher Better | Description |
|---|---|---|---|---|
| total_rides | COUNT(*) | rides | — | Total ride requests |
| acceptance_rate | AVG(was_accepted) × 100 | % | Yes | Driver acceptance rate |
| rider_cancel_rate | AVG(rider_cancelled) × 100 | % | No | Rider cancellation rate |
| completion_rate | AVG(was_completed) × 100 | % | Yes | Ride completion rate |
| avg_wait_time | AVG(wait_time_minutes) | min | No | Mean wait time |
| avg_surge | AVG(surge_multiplier) | × | No | Mean surge multiplier |
| high_demand_share | AVG(is_high_demand) × 100 | % | No | Share of high-demand rides |

### High-Demand Deterioration KPIs

| KPI | Comparison | Unit | Description |
|---|---|---|---|
| acceptance_rate | high vs normal | pp | Acceptance drop during high demand |
| rider_cancel_rate | high vs normal | pp | Cancel increase during high demand |
| avg_wait_time | high vs normal | min | Wait increase during high demand |
| avg_surge | high vs normal | × | Surge increase during high demand |

### City-Level KPIs

Same core metrics per city, compared against normal-demand baseline.

## Formatting Rules

| Type | Format | Example |
|---|---|---|
| Percentage | `{value:.1f}%` | 82.4% |
| Percentage points | `+{change:.1f} pp` | +6.8 pp |
| Minutes | `{value:.1f} min` | 11.2 min |
| Multiplier | `{value:.1f}x` | 1.8x |
| Count | `{value:,} rides` | 12,430 rides |

## Usage

```python
from roadies.visualization.kpis import calculate_kpis, build_kpi_cards

# Calculate KPIs
kpis = calculate_kpis(df)

# Overall KPIs
for kpi in kpis.overall:
    print(f"{kpi.label}: {kpi.formatted_value}")

# High-demand deterioration
for kpi in kpis.high_demand:
    print(f"{kpi.label}: {kpi.formatted_comparison}")

# City KPIs
for city, city_kpis in kpis.city.items():
    print(f"\n{city}:")
    for kpi in city_kpis:
        print(f"  {kpi.label}: {kpi.formatted_value} ({kpi.formatted_comparison})")

# Build visual cards
cards = build_kpi_cards(kpis.overall)
```

## Direction Logic

- **IMPROVED**: Value moved in better direction
- **DETERIORATED**: Value moved in worse direction
- **NEUTRAL**: No meaningful change

For rate metrics, percentage points are used for comparisons.
