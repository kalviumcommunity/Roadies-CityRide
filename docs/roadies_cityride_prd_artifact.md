# Roadies-CityRide — PRD Artifact

## 1. Problem
Rider experience appears to degrade during high-demand city-hours (above the 80th percentile of a city's own demand), but driver acceptance, cancellation, surge, and supply signals aren't currently combined into one view to explain why — diagnosis requires manually cross-referencing separate reports per city.

*No specific ₹ loss or time-saving figure is claimed — no verified baseline exists yet for either.*

## 2. Goal
Identify which cities degrade the most during high demand, and which behaviour (acceptance, supply, surge, or wait) is most associated with that degradation.

## 3. Stakeholders

| Type | Who |
|---|---|
| Primary Users | Operations Managers (6 cities) |
| Secondary Users | Business / Data Analysts |
| Data Owner | Dataset generator / data dictionary owner |
| Approver | Project reviewer / team lead |

## 4. Business Questions

| # | Business Question |
|---|---|
| 1 | Which cities have the worst rider experience? |
| 2 | How does demand affect driver acceptance? |
| 3 | Does surge pricing relate to rider cancellations? |
| 4 | What happens to rider experience during high demand? |
| 5 | Which cities degrade the most during high demand? |
| 6 | How does driver supply affect rider experience? |
| 7 | Are some drivers consistently associated with low acceptance? |
| 8 | What are the most common cancellation reasons? |

## 5. KPIs (Metric — Target — Timeline)

| KPI | Target | Timeline |
|---|---|---|
| Acceptance Rate | Flag cities below 70% | Full 90-day window |
| Rider Cancellation Rate | Flag cities above 15% | Full 90-day window |
| Completion Rate | Flag cities below 80% | Full 90-day window |
| Average Wait Time | Flag if high-demand wait exceeds normal by >50% | Per city-hour |
| Surge Multiplier | Flag if avg. high-demand surge exceeds 1.8x | High-demand hours only |
| Supply Ratio | Flag city-hours below 0.5 | Per city-hour |
| Experience Score | Flag cities below 0.6 during high demand | Normal vs. high demand |
| City Degradation Score | Rank all 6 cities; bottom 3 flagged | Full 90-day dataset |

*Thresholds are working values to validate once the dataset is loaded.*

## 6. Placeholder Formulas

```
Experience Score = 1 − (0.4 × normalized_wait_time
                        + 0.3 × rider_cancellation_rate
                        + 0.3 × (1 − completion_rate))

City Degradation Score = Experience Score(normal demand) − Experience Score(high demand)
```

Weights are illustrative; both will be finalized during analysis once real score distributions are visible.

## 7. High-Demand Rule
City-hour demand above the 80th percentile **for that specific city** → `is_high_demand = true`.

## 8. Dashboard Wireframe (v1)

```
[Total Requests] [Acceptance] [Cancellation] [Completion] [Avg Wait] [Avg Surge]

City Comparison (table + chart, sortable by degradation score)
High-Demand vs Normal-Demand (grouped bars / deltas)
Root-Cause View (Demand → Supply → Acceptance → Wait → Cancellation → Completion)
Cancellation Reasons (bar chart, filterable)

Sidebar: City | Date | Hour | Demand Period | Demand Level | Cancellation Reason
Interactions: click-to-filter by city, global sidebar filters, hover tooltips, reset button
```

## 9. Top Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Surge/cancellation correlation mistaken for causation | Medium | Medium | Label as association; show multiple signals together |
| Composite score hides which signal drives it | Medium | High | Always show component metrics alongside the score |
| Null `driver_id` on some rides | High | Low–Medium | Exclude nulls from driver-level metrics; document limitation |
| Unverified field definitions | Medium | High | Verify all fields against actual dataset before implementation |

## 10. Dataset Verification Status
All fields are now verified against the authoritative `docs/data_dictionary.md`. One open item remains: `request_timestamp` timezone is unspecified in the data dictionary and should be confirmed (e.g. IST) before hour-based derived fields (`hour`, `is_high_demand`) are implemented. Note also that `is_high_demand` is a **derived** field (80th-percentile rank), not the same as the raw `demand_level` category — both exist and serve different purposes.

## 11. Core Product Flow
```
Ingest → Clean & validate → Derive metrics → Compare cities → High-demand analysis → Root cause → Dashboard → Operational insight
```

## 12. Success Criteria
All 8 business questions answerable from the dashboard; all 6 cities ranked by degradation score; top 3 most degraded cities identified with surfaced root-cause behaviour; dashboard results traceable to the underlying dataset.
