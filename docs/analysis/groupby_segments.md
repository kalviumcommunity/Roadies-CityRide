# GroupBy Segment Analysis — Findings

> **Assignment #34** — GroupBy aggregation and segment insights
> **Dataset**: 50,000 synthetic ride requests across 6 cities (90 days)

---

## Grouping Dimensions

| Dimension | Values |
|---|---|
| city | Mumbai, Delhi, Bangalore, Hyderabad, Chennai, Pune |
| demand_period | low, normal, high |
| surge_category | none, low, moderate, high |
| acceptance_rate_band | well_above, above, near_baseline, below, well_below |
| cancellation_reason_category | wait_related, driver_behaviour, rider_decision, vehicle_related, other |
| time_period | night, morning, afternoon, evening |
| is_weekend | True, False |

## Minimum Segment Size

**Rule**: Segments with fewer than 100 observations are flagged for cautious interpretation. They appear in raw aggregation but are excluded from headline insights.

---

## Key Segment Findings

### 1. City × Demand Period

| City | Demand | Cancel Rate | Wait Time | Surge |
|---|---|---|---|---|
| Mumbai | high | 18.2% | 12.5 min | 2.1x |
| Mumbai | normal | 10.1% | 6.8 min | 1.2x |
| Delhi | high | 15.5% | 10.2 min | 1.8x |
| Delhi | normal | 9.2% | 6.1 min | 1.1x |
| Bangalore | high | 12.8% | 8.1 min | 1.5x |
| Hyderabad | high | 10.5% | 6.8 min | 1.3x |

**Finding**: Mumbai high-demand shows highest cancellation (18.2%) and wait (12.5 min). Hyderabad high-demand shows lowest values.

### 2. Surge Category × Wait Time

| Surge | Avg Wait | Cancel Rate |
|---|---|---|
| none | 5.2 min | 7.5% |
| low | 7.8 min | 10.2% |
| moderate | 11.5 min | 14.8% |
| high | 16.2 min | 19.5% |

**Finding**: Higher surge bands are associated with progressively longer waits and higher cancellation rates.

### 3. Acceptance Band × Completion

| Acceptance Band | Completion Rate | Cancel Rate |
|---|---|---|
| well_above | 82.5% | 6.2% |
| above | 78.1% | 8.5% |
| near_baseline | 72.3% | 11.8% |
| below | 65.2% | 16.5% |
| well_below | 55.8% | 24.2% |

**Finding**: Lower acceptance rates are strongly associated with lower completion and higher cancellation.

### 4. Time Period × Wait Time

| Time Period | Avg Wait | Surge |
|---|---|---|
| morning (6-12) | 7.2 min | 1.3x |
| afternoon (12-17) | 6.8 min | 1.2x |
| evening (17-21) | 9.5 min | 1.6x |
| night (0-6) | 8.1 min | 1.4x |

**Finding**: Evening shows highest wait and surge, consistent with commute demand.

---

## Rankings

### Highest Rider Cancellation Segments
1. Mumbai / high: 18.2%
2. Delhi / high: 15.5%
3. Pune / high: 14.2%
4. Bangalore / high: 12.8%
5. Chennai / high: 11.5%

### Lowest Completion Segments
1. well_below acceptance: 55.8%
2. high surge: 62.5%
3. Mumbai high-demand: 65.2%
4. below acceptance: 65.2%
5. Delhi high-demand: 68.5%

### Highest Wait Time Segments
1. Mumbai high-demand: 12.5 min
2. high surge: 16.2 min
3. Delhi high-demand: 10.2 min
4. evening: 9.5 min
5. Pune high-demand: 9.2 min

---

## Business Interpretation

### Observed Patterns
1. **Demand amplifies experience degradation**: High-demand periods show 40-60% higher cancellation and 30-50% longer waits across all cities
2. **Surge is a symptom, not a cause**: Surge correlates with wait time and cancellation, suggesting supply shortage drives both
3. **Acceptance is a leading indicator**: Lower acceptance rates precede higher cancellation and lower completion
4. **City resilience varies**: Hyderabad and Chennai show less degradation under high demand

### Possible Hypotheses
1. Cities with better supply-demand balance (Hyderabad) may have more driver availability during peaks
2. Evening demand spikes may reflect commute patterns that strain supply differently than random demand
3. The acceptance → cancellation pathway may be mediated by wait time

### Limitations
1. Synthetic data — real-world validation needed
2. Correlation, not causation — cannot claim surge causes cancellation
3. 90-day window — seasonal effects not captured

---

## Recommendations for Next Analysis

1. Test whether supply availability mediates the demand-experience relationship
2. Examine whether targeted supply increases in Mumbai could reduce degradation
3. Look for leading indicators that predict when segments will experience high deterioration
4. Investigate whether evening demand patterns differ fundamentally from daytime
