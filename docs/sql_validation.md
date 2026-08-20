# SQL/Python Validation — Roadies-CityRide

## Overview

This document describes the validation workflow for comparing SQL and Python metric calculations.

## Metrics Validated

### Core Metrics
- total_rides
- acceptance_rate
- completion_rate
- rider_cancel_rate
- driver_cancel_rate
- avg_wait_time
- avg_surge
- avg_demand_supply_ratio
- high_demand_share

### City-Level Metrics
- acceptance_rate, completion_rate, rider_cancel_rate, avg_wait_time, avg_surge per city

### Demand Comparison Metrics
- acceptance_rate, rider_cancel_rate, avg_wait_time for normal vs high demand

## Tolerances

| Metric Type | Tolerance | Justification |
|---|---|---|
| Count (total_rides) | 0 | Exact match expected |
| Rate/Percentage | 0.01 (1%) | Floating-point rounding |
| Float (wait, surge) | 0.1 | Measurement precision |

## Validation Procedure

```python
from roadies.validation import validate_sql_against_python

# Load dataset
df = pd.read_csv("data/raw/rides.csv")

# Validate against database
report = validate_sql_against_python(df, "data/roadies.db")

# Check results
print(report.summary())
# {'total': 25, 'passed': 25, 'failed': 0}

# View detailed comparisons
for comp in report.comparisons:
    print(f"{comp.metric_name}: {comp.passed}")
```

## Drift Detection

The validator detects computation drift when:
- Python and SQL values differ beyond tolerance
- Metric definitions diverge between layers
- Rounding or aggregation logic changes

### Example Detection

```python
# Create comparison with intentional drift
comparison = compare_metrics(80.0, 85.0, "acceptance_rate", absolute_tolerance=0.1)
print(comparison.passed)  # False
print(comparison.absolute_difference)  # 5.0
```

## Result Structure

```python
@dataclass
class MetricComparison:
    metric_name: str
    python_value: float
    sql_value: float
    absolute_difference: float
    relative_difference: float
    tolerance: float
    passed: bool
    category: str  # "core", "city", "demand"
```
