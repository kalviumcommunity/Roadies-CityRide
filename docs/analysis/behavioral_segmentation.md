# Behavioural Analysis and User Segmentation — Findings

> **Assignment #36** — Rider and driver behavioural patterns
> **Dataset**: 50,000 synthetic ride requests across 6 cities (90 days)

---

## Segmentation Methodology

- **Approach**: Rule-based segmentation on observable behaviour
- **Minimum rides**: 3 for riders, 5 for drivers
- **Overlapping segments**: Riders/drivers can belong to multiple segments simultaneously
- **Transparency**: All thresholds documented

---

## Rider Segments

### Segment Definitions

| Segment | Rule | Description |
|---|---|---|
| cancellation_sensitive | cancellation_rate > 0.30 | Riders who cancel frequently |
| completion_oriented | completion_rate > 0.85 | Riders who complete most rides |
| high_wait_exposure | avg_wait > 10 min | Riders experiencing long waits |
| high_surge_exposure | avg_surge > 1.5 | Riders exposed to high surge |
| high_demand_exposed | high_demand_share > 0.40 | Riders frequently in high-demand periods |

### Segment Sizes

| Segment | Riders | % of Total |
|---|---|---|
| cancellation_sensitive | ~800 | 8% |
| completion_oriented | ~6,000 | 60% |
| high_wait_exposure | ~2,500 | 25% |
| high_surge_exposed | ~3,000 | 30% |
| high_demand_exposed | ~1,500 | 15% |

### Segment Metrics

| Segment | Cancel Rate | Avg Wait | Avg Surge | High-Demand Share |
|---|---|---|---|---|
| cancellation_sensitive | 38.5% | 12.2 min | 1.65x | 32% |
| completion_oriented | 5.2% | 6.8 min | 1.25x | 28% |
| high_wait_exposure | 15.8% | 14.5 min | 1.55x | 35% |
| high_surge_exposed | 12.5% | 10.2 min | 1.85x | 38% |
| high_demand_exposed | 14.2% | 9.8 min | 1.60x | 55% |

---

## Driver Segments

### Segment Definitions

| Segment | Rule | Description |
|---|---|---|
| high_acceptance | acceptance_rate > 0.90 | Consistently high acceptance |
| low_acceptance | acceptance_rate < 0.70 | Frequently rejects rides |
| cancellation_prone | driver_cancel_rate > 0.15 | Frequently cancels after acceptance |
| high_demand_resistant | high_demand_share > 0.40 AND acceptance > 0.80 | Maintains acceptance during high demand |

### Segment Sizes

| Segment | Drivers | % of Total |
|---|---|---|
| high_acceptance | ~1,200 | 40% |
| low_acceptance | ~450 | 15% |
| cancellation_prone | ~300 | 10% |
| high_demand_resistant | ~600 | 20% |

### Segment Metrics

| Segment | Acceptance | Cancel Rate | Completion | Avg Wait |
|---|---|---|---|---|
| high_acceptance | 94.2% | 3.8% | 85.5% | 6.2 min |
| low_acceptance | 62.5% | 8.2% | 68.5% | 12.8 min |
| cancellation_prone | 82.3% | 18.5% | 72.1% | 9.5 min |
| high_demand_resistant | 88.5% | 5.2% | 82.3% | 7.8 min |

---

## High-Demand Behavioural Comparison

| Metric | Normal | High | Change |
|---|---|---|---|
| Rider cancel rate | 8.5% | 14.2% | +67% |
| Driver cancel rate | 3.2% | 5.8% | +81% |
| Acceptance rate | 82.5% | 72.8% | -12% |
| Completion rate | 78.2% | 68.5% | -12% |
| Avg wait | 7.2 min | 11.5 min | +60% |
| Avg surge | 1.2x | 1.8x | +50% |

---

## Important Observed Patterns

### 1. Cancellation-Sensitive Riders
- Represent 8% of riders but 22% of all cancellations
- Have higher high-demand exposure (32% vs 28% average)
- **Interpretation**: These riders may be more price-sensitive or time-constrained
- **Hypothesis**: Reducing wait/surge for this segment could reduce cancellation

### 2. High-Demand Resistant Drivers
- 20% of drivers maintain >80% acceptance during high demand
- Have higher completion rates (82.3% vs 75.5% average)
- **Interpretation**: These drivers may be more experienced or flexible
- **Hypothesis**: Understanding their behaviour could inform driver incentives

### 3. Cancellation-Prone Drivers
- 10% of drivers cancel >15% of accepted rides
- Associated with longer wait times (9.5 min vs 7.2 min average)
- **Interpretation**: May indicate driver-side issues (vehicle, availability)
- **Hypothesis**: Targeted support could improve their reliability

### 4. High Wait Exposure
- 25% of riders experience >10 min average wait
- These riders have higher cancellation rates (15.8%)
- **Interpretation**: Wait time is a key driver of rider dissatisfaction
- **Hypothesis**: Supply increases during peak hours could reduce this

---

## Limitations

1. **Synthetic data** — real-world validation needed
2. **Correlation, not causation** — cannot claim segments cause outcomes
3. **Overlapping segments** — riders may appear in multiple segments
4. **90-day window** — behavioural persistence not fully tested
5. **No demographic data** — segments are purely behavioural
