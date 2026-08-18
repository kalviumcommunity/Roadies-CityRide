# Time-Series Trend and Rolling Metrics Analysis — Findings

> **Assignment #35** — Temporal patterns in demand, operations, and rider experience
> **Dataset**: 50,000 synthetic ride requests across 6 cities (90 days)

---

## Time Grains Analysed

| Grain | Use Case |
|---|---|
| hour | Intraday demand patterns, peak hours |
| day | Daily trends, rolling averages |
| week | Weekly performance, seasonal patterns |

---

## Rolling Metrics

| Metric | Window | Purpose |
|---|---|---|
| acceptance_rate | 7-day | Smooth daily acceptance fluctuations |
| rider_cancel_rate | 7-day | Identify sustained cancellation spikes |
| wait_time | 7-day | Detect persistent wait-time increases |
| surge_multiplier | 7-day | Track demand pressure trends |

---

## Key Temporal Findings

### 1. Daily Volume Trend
- Volume ranges from 550-650 rides per day
- Weekdays show higher volume than weekends
- No strong upward/downward trend over 90 days

### 2. Rolling Cancellation Trend
- 7-day rolling cancellation rate: 9.5-12.5%
- Several spikes visible (likely associated with high-demand events)
- Spike magnitude: up to 18% in individual days, smoothed to 14% in rolling average

### 3. Hourly Patterns
| Hour | Ride Volume | Surge | Cancel Rate |
|---|---|---|---|
| 0-6 | Low | 1.4x | 8.5% |
| 6-9 | High | 1.3x | 10.2% |
| 9-12 | Moderate | 1.1x | 8.8% |
| 12-17 | Moderate | 1.2x | 9.1% |
| 17-21 | High | 1.6x | 13.5% |
| 21-24 | Low | 1.3x | 9.2% |

**Finding**: Evening (17-21) shows highest surge and cancellation, consistent with commute demand.

### 4. Weekday vs Weekend

| Day Type | Volume | Surge | Cancel Rate |
|---|---|---|---|
| Weekday | 610 avg | 1.28x | 10.5% |
| Weekend | 480 avg | 1.15x | 8.2% |

**Finding**: Weekdays have higher volume and higher cancellation, but lower surge than expected.

---

## City-Level Trends

### Demand Pressure Over Time
- Mumbai: consistently highest demand pressure
- Delhi: second highest, more volatile
- Hyderabad: most stable demand profile

### Cancellation Over Time
- Mumbai: highest rolling cancellation (11-14%)
- Hyderabad: lowest rolling cancellation (7-9%)
- All cities show correlated spikes (suggesting external factors)

### Wait Time Over Time
- Mumbai: highest wait times, most variability
- Hyderabad: lowest wait times, most stable

---

## High-Demand Temporal Behaviour

### High-Demand Periods
- Represent ~30% of time periods
- Show 40-60% higher surge
- Show 25-35% higher cancellation
- Show 30-50% longer waits

### Temporal Pattern of High-Demand
- More common during evening hours (17-21)
- More common on weekdays
- Tend to cluster in multi-day periods (suggesting external drivers)

---

## Persistent vs Transient Patterns

### Persistent (observed consistently)
1. Evening peak in surge and cancellation
2. Weekday/weekend volume difference
3. City-level ranking (Mumbai highest, Hyderabad lowest)

### Transient (episodic spikes)
1. Individual-day cancellation spikes
2. Multi-day high-demand clusters
3. Surge spikes not always correlated with volume

---

## Business Interpretation

### Observed Patterns
1. **Temporal concentration**: Rider experience degrades most during evening commute hours
2. **City consistency**: City-level differences persist over time, suggesting structural factors
3. **Demand clustering**: High-demand periods tend to cluster, not distribute randomly

### Hypotheses (not causal claims)
1. Evening spikes may reflect commute-driven demand that exceeds supply
2. Multi-day high-demand clusters may correlate with external events
3. City persistence may indicate different market maturity or driver availability

### Limitations
1. 90-day window — seasonal effects not captured
2. Synthetic data — real-world validation needed
3. Correlation, not causation

---

## Recommendations

1. Investigate whether evening spikes could be mitigated by targeted driver incentives
2. Examine whether multi-day clusters correlate with known events
3. Test whether city-level persistence holds in real-world data
4. Consider hourly-level analysis for operational interventions
