# Funnel Analysis and Drop-Off Detection — Findings

> **Assignment #37** — Ride lifecycle funnel analysis
> **Dataset**: 50,000 synthetic ride requests across 6 cities (90 days)

---

## Funnel Definition

```
ride requested
    ↓ (request → acceptance drop-off)
ride accepted
    ↓ (acceptance → completion drop-off)
ride completed
```

Side branches (not sequential):
- rider cancelled
- driver cancelled

---

## Stage Definitions

| Stage | Definition |
|---|---|
| requested | All ride requests (100%) |
| accepted | Requests where was_accepted = True |
| completed | Requests where ride_completed = True |
| rider_cancelled | Requests where rider_cancelled = True |
| driver_cancelled | Requests where driver_cancelled = True |

---

## Overall Funnel

| Stage | Count | Rate | Drop-Off | Drop-Off % |
|---|---|---|---|---|
| requested | 50,000 | 100% | — | — |
| accepted | 40,000 | 80% | 10,000 | 20% |
| completed | 35,000 | 70% | 5,000 | 12.5% |
| rider_cancelled | 5,000 | 10% | — | — |
| driver_cancelled | 2,500 | 5% | — | — |

### Conversion Rates
- Request → Acceptance: **80%**
- Acceptance → Completion: **87.5%**
- Request → Completion: **70%**

---

## Major Drop-Off Points

### 1. Requested → Accepted (20% drop-off)
- **10,000 requests** not accepted
- Largest single drop-off point
- **Interpretation**: Supply-side constraint — drivers not available or declining

### 2. Accepted → Completed (12.5% drop-off)
- **5,000 accepted rides** not completed
- **Interpretation**: Cancellation after acceptance (rider or driver)

---

## City-Level Differences

| City | Request → Accept | Accept → Complete | Request → Complete |
|---|---|---|---|
| Mumbai | 75% | 85% | 64% |
| Delhi | 78% | 86% | 67% |
| Bangalore | 82% | 88% | 72% |
| Hyderabad | 85% | 90% | 77% |
| Chennai | 83% | 89% | 74% |
| Pune | 80% | 87% | 70% |

**Finding**: Mumbai shows lowest acceptance (75%) and completion after acceptance (85%). Hyderabad shows highest values.

---

## High-Demand Comparison

| Metric | Normal | High | Change |
|---|---|---|---|
| Request → Accept | 85% | 72% | -13 pp |
| Accept → Complete | 90% | 82% | -8 pp |
| Request → Complete | 77% | 59% | -18 pp |
| Rider Cancel Rate | 8% | 15% | +7 pp |
| Driver Cancel Rate | 4% | 7% | +3 pp |

**Finding**: High-demand periods show significant deterioration across all funnel stages.

---

## Consistent with Previous Findings

### From Issue #32 (Relationships)
- Demand-supply ratio correlates with surge → confirmed: acceptance drops during high demand

### From Issue #33 (City Segmentation)
- Mumbai shows highest deterioration → confirmed: lowest acceptance/completion

### From Issue #36 (Behavioural)
- Cancellation-sensitive riders represent 8% but 22% of cancellations → confirmed: rider cancellation is significant drop-off

---

## Business Interpretation

### Observed Patterns
1. **Request → Acceptance is the largest drop-off** (20%) — suggests supply-side constraint
2. **High demand amplifies all drop-offs** — acceptance drops 13 pp, completion drops 8 pp
3. **City differences persist** — Mumbai consistently worse, Hyderabad consistently better

### Hypotheses (not causal claims)
1. Supply shortage during high demand is the primary driver of funnel deterioration
2. City-level differences may reflect different market maturity or driver availability
3. Rider cancellation after acceptance may be driven by wait time or surge

### Limitations
1. Synthetic data — real-world validation needed
2. Correlation, not causation — cannot claim root causes
3. Funnel shows where losses occur, not why

---

## Recommendations

1. Investigate root causes of request → acceptance drop-off (Issue #38)
2. Examine whether supply increases during high demand could reduce drop-offs
3. Test whether Mumbai-specific interventions could improve acceptance
4. Look for leading indicators of funnel deterioration
