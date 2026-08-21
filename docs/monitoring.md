# Alert Monitoring and Pipeline — Roadies-CityRide

## Overview

Reusable monitoring layer that runs the analytical pipeline and evaluates operational alert thresholds.

## Running the Pipeline

```bash
uv run python scripts/run_pipeline.py
```

## Pipeline Stages

| Stage | Description |
|---|---|
| 1. Load | Load dataset from CSV |
| 2. Feature Engineering | Apply demand/surge/acceptance/cancellation/experience/demand-period features |
| 3. KPI Calculation | Calculate core, high-demand, and city-level KPIs |
| 4. Alert Evaluation | Check thresholds and generate structured alerts |

## Alert Rules

| Alert | Metric | Default Threshold | Severity |
|---|---|---|---|
| High-demand rider cancel | rider_cancel_rate | > 20% | HIGH |
| High-demand acceptance low | acceptance_rate | < 70% | CRITICAL |
| Acceptance deterioration | acceptance_deterioration | < -10pp | HIGH |
| Wait time high | avg_wait_time | > 15 min | HIGH |
| Wait time deterioration | wait_time_deterioration | > 5 min | WARNING |
| Surge high | avg_surge | > 2.0x | HIGH |
| City-level variants | Same metrics | Same thresholds | Per city |

## Severity Levels

| Level | Value | Meaning |
|---|---|---|
| INFO | info | Normal operation |
| WARNING | warning | Approaching threshold |
| HIGH | high | Threshold exceeded |
| CRITICAL | critical | Severe degradation |

## Configuration

Thresholds are configurable via `MonitoringThresholds`:

```python
from roadies.monitoring import MonitoringThresholds, evaluate_alerts

t = MonitoringThresholds(
    rider_cancel_high=20.0,
    acceptance_low=70.0,
    wait_time_high=15.0,
    surge_high=2.0,
    min_sample_size=30,
)

result = evaluate_alerts(df, t)
```

## Minimum Sample Size

Alerts are only evaluated when high-demand observations ≥ `min_sample_size` (default: 30).

## Alert Result Structure

```python
@dataclass
class Alert:
    name: str
    severity: Severity
    metric: str
    observed_value: float
    threshold: float
    comparison: str
    city: str | None
    period: str | None
    message: str
    triggered: bool
```
