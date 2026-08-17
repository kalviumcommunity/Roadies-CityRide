# Feature Distribution Analysis — Findings

> **Assignment #31** — Exploratory analysis of engineered ride-sharing features
> **Dataset**: 50,000 synthetic ride requests across 6 cities (90 days)

---

## Key Distribution Patterns

### Demand & Supply

- **Requested rides per city-hour** range from ~10 to ~200, with a right-skewed distribution.
- **Available drivers** follow a similar pattern but with lower variance.
- **Demand-supply ratio** is mostly between 2–6 rides per driver, with occasional spikes above 10.

### Surge Pricing

- **Surge multiplier** ranges from 1.0x to 5.0x, with the majority at 1.0x (no surge).
- About 30–40% of rides experience some surge pricing.
- **Surge intensity** (normalised 0–1) shows a bimodal distribution: concentrated at 0 and around 0.3–0.5.

### Wait Time

- **Wait time** is right-skewed: most rides wait 3–10 minutes, with a long tail to 60+ minutes.
- The median wait is approximately 6–8 minutes across cities.

### Driver Acceptance

- **Driver acceptance rate** clusters around 0.75–0.90, with a mean near 0.80.
- Acceptance rates below 0.60 are rare but present.

---

## City-Level Differences

| City | Ride Volume | Avg Surge | Avg Wait | Acceptance |
|---|---|---|---|---|
| Mumbai | High | Higher | Higher | Moderate |
| Delhi | High | Moderate | Moderate | Moderate |
| Bangalore | Medium | Moderate | Lower | Higher |
| Hyderabad | Medium | Lower | Lower | Higher |
| Chennai | Lower | Lower | Lower | Higher |
| Pune | Lower | Lower | Lower | Moderate |

**Observations**: Mumbai and Delhi show higher surge and wait times, consistent with higher demand density. Bangalore, Hyderabad, and Chennai show relatively better supply-demand balance.

---

## High-Demand vs Normal-Demand

| Metric | Normal | High | Change |
|---|---|---|---|
| Surge multiplier | ~1.1x | ~1.8x | +60% |
| Wait time | ~6 min | ~10 min | +67% |
| Acceptance rate | ~0.82 | ~0.75 | -9% |
| Available drivers | ~40 | ~25 | -38% |

**Key finding**: Under high demand, surge increases ~60%, wait times increase ~67%, and acceptance rates drop ~9%. This suggests supply pressure degrades rider experience during high-demand periods.

---

## Cancellation Patterns

- **Rider cancellation rate** increases during high demand (~12% vs ~8% normal).
- **Primary cancellation reasons**: "Long wait time" (35%), "Changed mind" (30%), "Other" (20%).
- Rider cancellations before acceptance are more common during high demand.

---

## Experience Classification

- **completed_good**: ~55% of rides
- **completed_elevated_wait**: ~15% of rides
- **completed_high_surge**: ~10% of rides
- **rider_cancelled**: ~10% of rides
- **driver_cancelled**: ~3% of rides
- **not_accepted**: ~7% of rides

---

## Important Observations

1. **Supply constraint is the primary driver**: High demand periods show significantly fewer available drivers per ride request, creating a cascade of higher surge, longer waits, and more cancellations.

2. **City-level variation exists**: Not all cities degrade equally under high demand. Cities with better supply-demand balance (Hyderabad, Chennai) show less experience degradation.

3. **Cancellation is demand-responsive**: Rider cancellations increase during high demand, primarily driven by wait time. This suggests wait time is a key experience pain point.

4. **Surge acts as a signal**: Higher surge correlates with worse experience metrics, suggesting surge is a symptom of supply pressure rather than an independent factor.

5. **No causal claims**: These are correlational patterns. The next analysis stage should investigate causal pathways.

---

## Recommendations for Next Analysis

1. Investigate city-level degradation patterns in detail
2. Test whether supply availability mediates the demand-experience relationship
3. Examine whether cancellation reasons change meaningfully across demand levels
4. Look for threshold effects where experience degradation accelerates
