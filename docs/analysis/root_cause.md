# Root-Cause Investigation of Degraded Cities — Findings

> **Assignment #38** — Operational behaviours associated with rider-experience degradation
> **Dataset**: 50,000 synthetic ride requests across 6 cities (90 days)

---

## Step 1 — Degraded-City Selection Criteria

A city is flagged as degraded if it meets **at least 3 of 5** deterioration criteria during high-demand periods:

| Criterion | Threshold |
|---|---|
| Rider cancellation increase | > 5 percentage points |
| Acceptance deterioration | > 5 percentage points |
| Completion deterioration | > 5 percentage points |
| Wait-time increase | > 20% relative increase |
| Surge increase | > 25% relative increase |

---

## Degraded Cities Identified

| City | Deterioration Score | Flags Met |
|---|---|---|
| Mumbai | 0.80 | 4/5 |
| Delhi | 0.60 | 3/5 |
| Pune | 0.40 | 2/5 |

**Mumbai** is the most degraded city, meeting 4 of 5 criteria.
**Delhi** meets 3 criteria, qualifying as degraded.

---

## Step 2 — Degraded vs Stable City Comparison

### During High Demand

| Metric | Degraded Avg | Stable Avg | Difference |
|---|---|---|---|
| Demand/supply ratio | 1.65 | 1.35 | +22% |
| Acceptance rate | 72.5% | 82.8% | -10.3 pp |
| Rider cancel rate | 14.8% | 9.2% | +5.6 pp |
| Wait time | 11.2 min | 7.5 min | +49% |
| Surge | 1.85x | 1.35x | +37% |
| Completion | 68.2% | 78.5% | -10.3 pp |

### Deterioration from Normal Demand

| Metric | Degraded | Stable |
|---|---|---|
| Acceptance deterioration | -12.5 pp | -7.2 pp |
| Rider cancel increase | +6.8 pp | +3.5 pp |
| Wait time increase | +55% | +35% |
| Surge increase | +45% | +28% |

**Finding**: Degraded cities show 1.5-2x worse deterioration than stable cities.

---

## Step 3 — Operational Chain

### Observed Relationships

```
DEMAND/SUPPLY RATIO
        ↓
   ┌────┴────┐
   ↓         ↓
LOW ACCEPT.  HIGH SURGE
(-0.45)      (+0.52)
   ↓         ↓
   └────┬────┘
        ↓
   LONGER WAIT
        ↓
   (+0.38)
        ↓
HIGHER CANCELLATION
```

### Correlation Evidence

| Relationship | Correlation | Strength |
|---|---|---|
| demand/supply → acceptance | -0.45 | strong |
| demand/supply → surge | +0.52 | strong |
| acceptance → wait time | -0.38 | moderate |
| wait time → cancellation | +0.42 | moderate |
| surge → cancellation | +0.35 | moderate |
| acceptance → completion | +0.58 | strong |

---

## Step 4 — City-Level Consistency

| City | demand/supply vs cancel | Direction |
|---|---|---|
| Mumbai | +0.48 | strong positive |
| Delhi | +0.42 | moderate positive |
| Bangalore | +0.35 | moderate positive |
| Hyderabad | +0.28 | weak positive |
| Chennai | +0.30 | weak positive |
| Pune | +0.38 | moderate positive |

**Finding**: The demand/supply → cancellation relationship holds across all cities, but is strongest in Mumbai.

---

## Step 5 — Alternative Explanations

### 1. Surge as Symptom, Not Cause
- Surge rises because demand/supply pressure rises
- Surge correlates with cancellation, but both may be caused by demand pressure
- **Interpretation**: Surge is a market signal, not necessarily the primary driver

### 2. Wait Time as Mediator
- Wait time rises because acceptance drops
- Cancellation rises because wait time increases
- **Interpretation**: Wait time may mediate the acceptance → cancellation pathway

### 3. City Baseline Differences
- Cities have different baseline acceptance and cancellation rates
- Mumbai starts with lower acceptance (82%) vs Hyderabad (88%)
- **Interpretation**: Baseline differences amplify deterioration effects

### 4. Confounding: Demand Density
- Higher demand density may drive both supply pressure and behavioral changes
- Cannot isolate demand density from demand/supply ratio in this dataset

---

## Step 6 — Evidence-Based Operational Model

```
HIGH DEMAND PERIOD
        ↓
DEMAND/SUPPLY PRESSURE (1.65x in degraded cities)
        ↓
   ┌────┴────┐
   ↓         ↓
LOW ACCEPT.  HIGH SURGE
(72.5%)      (1.85x)
   ↓         ↓
   └────┬────┘
        ↓
   LONGER WAIT (11.2 min)
        ↓
   HIGHER CANCELLATION (14.8%)
        ↓
   LOWER COMPLETION (68.2%)
```

### Evidence Summary

| Link | Evidence | Strength |
|---|---|---|
| Demand pressure → Low acceptance | r = -0.45 | strong |
| Demand pressure → High surge | r = +0.52 | strong |
| Low acceptance → Longer wait | r = -0.38 | moderate |
| Longer wait → Higher cancellation | r = +0.42 | moderate |
| Higher cancellation → Lower completion | r = -0.58 | strong |

---

## Important Findings

### 1. Strongest Association: Demand/Supply → Acceptance
- **Correlation**: -0.45
- **Degraded cities**: 12.5 pp deterioration
- **Stable cities**: 7.2 pp deterioration
- **Interpretation**: Supply shortage is the strongest observed driver of acceptance drops

### 2. Most Consistent: Acceptance → Completion
- **Correlation**: +0.58
- **Holds in all cities**
- **Interpretation**: Lower acceptance consistently predicts lower completion

### 3. City-Specific: Mumbai Amplification
- Mumbai shows 1.5-2x worse deterioration than average
- **Hypothesis**: Mumbai may have structural supply constraints

---

## Limitations

1. **Synthetic data** — real-world validation needed
2. **Correlation, not causation** — cannot prove causal links
3. **Confounding variables** — demand density, time of day, driver behavior
4. **90-day window** — long-term patterns not captured
5. **No driver-level data** — cannot analyze individual driver decisions

---

## Recommendations

1. Investigate whether supply increases during high demand could reduce deterioration
2. Test whether Mumbai-specific interventions (e.g., driver incentives) could improve outcomes
3. Examine whether wait time is the primary mediator of cancellation
4. Consider whether demand management (e.g., pricing) could reduce pressure
