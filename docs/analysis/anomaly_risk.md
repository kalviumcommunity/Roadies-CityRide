# Anomaly Detection and Operational Risk Analysis — Findings

> **Assignment #39** — Identifying unusual conditions and elevated risk
> **Dataset**: 50,000 synthetic ride requests across 6 cities (90 days)

---

## Anomaly Methods

| Method | Description | Use Case |
|---|---|---|
| z-score | Values > 2 standard deviations from mean | Global anomaly detection |
| IQR | Values outside 1.5 × IQR from quartiles | Robust outlier detection |
| City-relative | Values unusual for specific city | City-specific anomalies |
| Threshold-based | Risk classification by metric thresholds | Risk level assignment |

---

## Risk Classification Rules

| Level | Criteria |
|---|---|
| normal | All metrics within expected ranges |
| elevated | Any metric crosses elevated threshold |
| high | Any metric crosses high threshold |
| critical | Any metric crosses critical threshold |

### Thresholds

| Metric | Elevated | High | Critical |
|---|---|---|---|
| demand/supply ratio | > 1.5 | > 2.0 | > 2.5 |
| surge multiplier | > 1.5 | > 2.0 | > 2.5 |
| wait time | > 10 min | > 15 min | > 20 min |
| rider cancel rate | > 15% | > 20% | > 25% |
| acceptance rate | < 75% | < 70% | < 65% |
| completion rate | < 75% | < 70% | < 65% |

---

## Anomaly Counts

### Global Anomalies
| Metric | Count | % of Total |
|---|---|---|
| demand_supply_ratio | ~2,500 | 5% |
| surge_multiplier | ~2,800 | 5.6% |
| wait_time_minutes | ~3,200 | 6.4% |
| rider_cancelled | ~5,000 | 10% |

### Risk Level Distribution
| Level | Count | % |
|---|---|---|
| normal | 38,000 | 76% |
| elevated | 7,500 | 15% |
| high | 3,000 | 6% |
| critical | 1,500 | 3% |

---

## City Anomaly Frequency

| City | Anomaly Rate | Critical Count | Risk Level |
|---|---|---|---|
| Mumbai | 28% | 4.2% | highest |
| Delhi | 22% | 2.8% | high |
| Pune | 18% | 1.5% | moderate |
| Bangalore | 15% | 1.2% | moderate |
| Chennai | 13% | 0.8% | low |
| Hyderabad | 11% | 0.5% | lowest |

**Finding**: Mumbai has 2.5x higher anomaly rate than Hyderabad.

---

## High-Risk Periods

- **Total high-risk periods**: ~450 (out of ~2,160 hours)
- **High-risk during high demand**: 65% of high-risk periods occur during high-demand hours
- **Multiple signals**: 35% of high-risk periods have >1 risk signal simultaneously

---

## High-Demand Anomaly Behaviour

| Metric | Normal Period Anomaly Rate | High-Demand Anomaly Rate | Change |
|---|---|---|---|
| demand_supply_ratio | 3% | 12% | +9 pp |
| surge_multiplier | 4% | 14% | +10 pp |
| wait_time_minutes | 5% | 15% | +10 pp |
| rider_cancelled | 8% | 18% | +10 pp |

**Finding**: Anomaly rates increase 2-3x during high-demand periods.

---

## Relationship with Issue #38 Operational Model

### Consistent Findings
1. **Demand pressure → anomalies**: High demand/supply ratio is the most frequent anomaly trigger
2. **Mumbai amplification**: Mumbai shows highest anomaly frequency, consistent with root-cause findings
3. **Multiple signals**: Risk periods often show simultaneous anomalies, consistent with operational chain

### New Insights
1. **Temporal clustering**: Anomalies cluster during high-demand hours (not random)
2. **City-specific baselines**: City-relative anomalies reveal cities where values are unusual for that specific market
3. **Risk escalation**: 3% of observations are "critical" — these coincide with worst rider experience

---

## Important Limitations

1. **Threshold-dependent**: Risk classification depends on chosen thresholds
2. **Synthetic data**: Real-world validation needed
3. **Not causal**: Anomalies indicate unusual conditions, not necessarily failures
4. **Baseline sensitivity**: City-relative anomalies depend on sufficient city-level data
5. **Multiple signals**: Combined risk signals may overlap or confound
