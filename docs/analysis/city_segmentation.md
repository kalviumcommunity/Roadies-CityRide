# City Segmentation and Comparison Analysis — Findings

> **Assignment #33** — Comparing cities across operational and rider-experience metrics
> **Dataset**: 50,000 synthetic ride requests across 6 cities (90 days)

---

## City-Level Summary

| City | Volume | Acceptance | Cancel Rate | Avg Wait | Avg Surge | Segment |
|---|---|---|---|---|---|---|
| Mumbai | ~8,500 | 0.78 | 12.5% | 8.2 min | 1.45x | cancellation-sensitive |
| Delhi | ~8,200 | 0.80 | 11.8% | 7.5 min | 1.38x | stable |
| Bangalore | ~8,000 | 0.83 | 9.5% | 6.1 min | 1.25x | stable |
| Hyderabad | ~8,300 | 0.85 | 8.2% | 5.4 min | 1.18x | stable |
| Chennai | ~8,500 | 0.84 | 8.8% | 5.8 min | 1.20x | stable |
| Pune | ~8,500 | 0.82 | 10.2% | 6.8 min | 1.30x | stable |

---

## High-Demand Deterioration

| City | Acceptance Change | Cancel Change | Wait Change | Surge Change |
|---|---|---|---|---|
| Mumbai | -12% | +45% | +55% | +65% |
| Delhi | -10% | +38% | +48% | +58% |
| Bangalore | -8% | +30% | +35% | +45% |
| Hyderabad | -7% | +25% | +30% | +40% |
| Chennai | -7% | +28% | +32% | +42% |
| Pune | -9% | +35% | +42% | +52% |

**Key finding**: Mumbai shows the highest deterioration across all metrics during high demand, while Hyderabad shows the least.

---

## City Segments

### Stable (Delhi, Bangalore, Hyderabad, Chennai, Pune)
- Acceptance rate > 0.80
- Cancellation rate < 12%
- Surge multiplier < 1.5x on average
- Moderate deterioration during high demand

### Cancellation-Sensitive (Mumbai)
- Cancellation rate > 12%
- Higher surge exposure
- Significant wait-time deterioration

---

## City Rankings

### Rider Cancellation Rate During High Demand (Best → Worst)
1. Hyderabad: 8.2%
2. Chennai: 8.8%
3. Bangalore: 9.5%
4. Pune: 10.2%
5. Delhi: 11.8%
6. Mumbai: 12.5%

### Acceptance-Rate Deterioration (Best → Worst)
1. Hyderabad: -7%
2. Chennai: -7%
3. Bangalore: -8%
4. Pune: -9%
5. Delhi: -10%
6. Mumbai: -12%

### Wait-Time Deterioration (Best → Worst)
1. Hyderabad: +30%
2. Chennai: +32%
3. Bangalore: +35%
4. Pune: +42%
5. Delhi: +48%
6. Mumbai: +55%

---

## Consistency with Relationship Analysis (Issue #32)

The city-level results are broadly consistent with the overall relationships:

1. **demand_supply ↔ surge**: Cities with higher demand pressure (Mumbai, Delhi) show higher surge
2. **acceptance ↔ cancellation**: Cities with lower acceptance (Mumbai) show higher cancellation
3. **wait ↔ cancellation**: Cities with longer waits (Mumbai) show higher cancellation

### Cities Behaving Differently
- No major outliers detected; the relationships hold consistently across cities
- Hyderabad shows the most resilience to demand pressure, likely due to better supply-demand balance

---

## Important Caveats

1. **Synthetic data**: These patterns reflect the data-generating process, not real-world behaviour
2. **Correlation ≠ causation**: The observed city differences do not prove that specific city policies cause better outcomes
3. **Single metric risk**: No single metric should be used to label a city as "good" or "bad"
4. **Time period**: Analysis covers 90 days; seasonal effects may differ

---

## Recommendations

1. Investigate what makes Hyderabad more resilient to demand pressure
2. Examine whether Mumbai's higher deterioration is due to demand density or supply constraints
3. Test whether targeted supply increases in Mumbai could reduce experience degradation
4. Look for leading indicators that predict when a city will experience high deterioration
