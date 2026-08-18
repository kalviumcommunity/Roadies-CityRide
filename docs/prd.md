# Roadies-CityRide — Product Requirements Document

## 1. Business Problem

**Problem**

Roadies-CityRide operates across 6 cities using a ride-level dataset covering approximately 90 days and 50,000–100,000 ride records.

The project needs to determine whether rider experience degrades during high-demand city-hours, defined as hours where demand is above the 80th percentile of that city's own demand.

The available data contains driver acceptance, rider and driver cancellations, surge pricing, waiting time, completion, demand, and supply signals. However, these signals need to be analysed together to determine which city-level behaviours are most associated with degraded rider experience.

The product will provide a single analytical view instead of requiring users to manually compare separate metrics and reports.

**Goal**

Identify:
- Which cities experience the greatest degradation during high-demand periods.
- Which operational behaviours — acceptance, supply, surge, or wait time — are most associated with that degradation.

**Primary Users**

Operations Managers responsible for the 6 cities in the project dataset.

**Success Criteria**

The product will be considered successful when:
- All 8 defined business questions can be answered from the dashboard.
- All 6 cities can be ranked by City Degradation Score.
- The 3 most degraded cities can be identified.
- The dashboard surfaces the key behaviours associated with degradation.
- Dashboard results match validated Python/SQL analysis.

**Important:** The PRD does not claim a specific financial loss or a pre-existing measured time saving because no verified baseline for either has been provided.

## 2. Stakeholders

| Stakeholder Type | Who | Responsibility |
|---|---|---|
| Primary Users | Operations Managers | Compare cities and investigate rider-experience degradation |
| Secondary Users | Business / Data Analysts | Analyse patterns and validate findings |
| Data Owner | Team member responsible for dataset generator/data dictionary | Confirm data fields, definitions, quality, and generation logic |
| Approver | Project reviewer / team lead | Review and approve the PRD, artifact, and dashboard requirements |

The four stakeholder categories follow the Kalvium requirement of Primary Users, Secondary Users, Data Owners, and Approvers.

## 3. Business Impact

**Operational Impact**

Operations Managers need to evaluate multiple operational signals when investigating city-level rider experience. This product combines those signals into one dashboard covering all 6 cities, allowing users to compare cities and identify the 3 most degraded cities during high-demand periods.

**Revenue / Cost Impact**

The dataset contains ride outcomes and fare-related information, but the project does not currently have a verified monetary-loss baseline. Therefore, this PRD does not claim a specific ₹ impact. Instead, the product will identify unsuccessful ride outcomes such as rider cancellations, driver cancellations, and incomplete rides — which can be used for further business investigation.

**User Experience Impact**

The product will measure rider-facing changes in average wait time, rider cancellation rate, completion rate, and surge multiplier between normal-demand and high-demand city-hours.

## 4. Dataset & Data Source Documentation

**Dataset Overview**

| Property | Details |
|---|---|
| Source | Project synthetic ride-sharing dataset |
| Grain | One row per ride request |
| Size | Approximately 50,000–100,000 rows |
| Time period | 90 days |
| Cities | 6 |
| Primary Key | `ride_id` |
| Format | CSV/JSON |
| Refresh | Static, pre-generated dataset |

**Field Documentation — verified against `docs/data_dictionary.md` (confirmed with Data Owner)**

| Field | Type | Nullable | Verified | Valid Range / Notes |
|---|---|---|---|---|
| `ride_id` | String | No | ✅ Verified | Format `R-NNNNNN`; unique primary key |
| `rider_id` | String | No | ✅ Verified | Format `RDR-NNNN`; logical FK, not previously listed in this PRD |
| `driver_id` | String | Yes | ✅ Verified | Format `DRV-NNNN`; null when unassigned |
| `city` | String | No | ✅ Verified | 6 fixed values: Mumbai, Delhi, Bangalore, Hyderabad, Chennai, Pune |
| `request_timestamp` | Datetime (ISO 8601) | No | ✅ Verified | Range: 2025-07-01 to 2025-09-28 |
| `accepted` | Boolean | No | ✅ Verified | — |
| `completed` | Boolean | No | ✅ Verified | Implies `accepted = true` |
| `cancelled_by_rider` | Boolean | No | ✅ Verified | May occur before or after acceptance |
| `cancelled_by_driver` | Boolean | No | ✅ Verified | Only possible if `accepted = true` |
| `cancellation_reason` | String | Yes | ✅ Verified | Values: Long wait time, Driver rude, Changed mind, Vehicle quality, Other; null when not cancelled |
| `driver_acceptance_rate` | Float | Yes | ✅ Verified | Range 0.0–1.0; null when `driver_id` is null |
| `driver_rating` | Float | Yes | ✅ Verified | Range 1.0–5.0; null when `driver_id` is null |
| `city_hour_requested_rides` | Integer | No | ✅ Verified | Range 1–500; denormalised city-hour context |
| `city_hour_available_drivers` | Integer | No | ✅ Verified | Range 0–300; denormalised city-hour context |
| `demand_level` | String | No | ✅ Verified | Categorical: low, medium, high, critical — generated directly by the synthetic generator, **not** derived later (see note below) |
| `surge_multiplier` | Float | No | ✅ Verified | Range 1.0–5.0; 1.0 = no surge |
| `base_fare` | Float | No | ✅ Verified | Range 50.0–500.0 INR |
| `wait_time_minutes` | Float | Yes | ✅ Verified | Range 0.0–60.0; null when `accepted = false` |
| `trip_duration_minutes` | Float | Yes | ✅ Verified | Range 0.0–120.0; null when `completed = false` |
| `trip_distance_km` | Float | Yes | ✅ Verified | Range 0.0–50.0; null when `completed = false` |

**Corrected assumption:** the earlier draft of this PRD implied `is_high_demand` might be a raw field. It is **not** — it is a derived field computed in feature engineering (percentile rank of `city_hour_requested_rides` within each city, thresholded at the 80th percentile). `demand_level`, by contrast, *is* raw and generated directly by the generator; the two are related but not identical, and the PRD's high-demand rule (Section 6) uses the derived percentile-based `is_high_demand`, not the raw `demand_level` category.

**Derived fields relevant to this PRD (not in raw data, computed later):** `is_high_demand`, `demand_percentile`, `demand_period`, `supply_ratio`, `estimated_fare`, `experience_score`, plus category/flag fields (e.g. `wait_time_severity`, `surge_category`, `cancellation_type`). Full list lives in the data dictionary's "Derived Fields" section.

**Data Verification Rule**

All fields above have been checked against the authoritative `docs/data_dictionary.md`. This satisfies Kalvium's requirement that data fields, quality, ownership, and refresh information be confirmed rather than assumed.

**Timezone**

`request_timestamp` is stored as ISO 8601; the data dictionary does not specify a timezone explicitly. This remains a small open item — the team should confirm (e.g., IST) before hour-of-day analysis, since bucketing by "hour" is meaningless without knowing the reference timezone.

## 5. KPIs & Success Metrics

Kalvium specifies that each KPI should contain: **Metric + Measurement Method + Numeric Target + Timeline**.

| KPI | Measurement Method | Target | Timeline |
|---|---|---|---|
| Acceptance Rate | Accepted rides ÷ total ride requests | Flag cities below 70% | Full 90-day window |
| Rider Cancellation Rate | Rider cancellations ÷ total requests | Flag cities above 15% | Full 90-day window |
| Completion Rate | Completed rides ÷ total requests | Flag cities below 80% | Full 90-day window |
| Average Wait Time | Mean `wait_time_minutes` | Flag if high-demand wait is >50% higher than normal | Per city-hour |
| Surge Multiplier | Average `surge_multiplier` during high demand | Flag if average exceeds 1.8x | High-demand hours |
| Supply Ratio | Available drivers ÷ requested rides | Flag city-hours below 0.5 | Per city-hour |
| Experience Score | Normalized composite of wait time, completion, and rider cancellation | Flag below 0.6 during high demand | Normal vs. high demand |
| City Degradation Score | Weighted change in Experience Score between normal and high demand | Rank all 6 cities; flag bottom 3 | Full 90-day dataset |

**KPI Threshold Note**

The numerical thresholds above are working project thresholds and must be validated against the actual dataset during analysis.

**Experience Score — placeholder formula**

The exact weighting and normalization will be finalized during the analysis phase and documented before implementation. As a starting placeholder, so the reviewer can see the intended structure rather than an unspecified black box:

```
Experience Score = 1 − (
    0.4 × normalized_wait_time
  + 0.3 × rider_cancellation_rate
  + 0.3 × (1 − completion_rate)
)
```

Where `normalized_wait_time` is `wait_time_minutes` scaled to a 0–1 range (e.g., min-max scaled per city). Score ranges from 0 (worst) to 1 (best). Weights (0.4 / 0.3 / 0.3) are illustrative and will be reviewed once real score distributions are visible — no arbitrary weighting is treated as final at the PRD stage.

**City Degradation Score — placeholder formula**

The exact weighting/calculation method will be finalized during analysis and documented before implementation. As a placeholder:

```
City Degradation Score = Experience Score(normal demand) − Experience Score(high demand)
```

A higher positive value means a bigger drop in experience when demand goes from normal to high — i.e., a more degraded city. This will be re-evaluated once the Experience Score weighting above is finalized, since Degradation Score is directly derived from it.

## 6. High-Demand Definition

A city-hour is classified as high demand when:

```
City-hour demand > the 80th percentile of demand for that specific city.

City-hour demand
       ↓
Calculate 80th percentile for that city
       ↓
Demand > city-specific 80th percentile
       ↓
is_high_demand = true
```

The city-specific rule is retained so that cities are evaluated relative to their own demand patterns.

## 7. Business Questions

| ID | Business Question |
|---|---|
| BQ1 | Which cities have the worst rider experience? |
| BQ2 | How does demand affect driver acceptance? |
| BQ3 | Does surge pricing relate to rider cancellations? |
| BQ4 | What happens to rider experience during high-demand periods? |
| BQ5 | Which cities degrade the most during high-demand periods? |
| BQ6 | What is the relationship between driver supply and rider experience? |
| BQ7 | Are some drivers consistently associated with low acceptance rates? |
| BQ8 | What are the most common reasons for cancellations? |

## 8. Rider Experience Model

Rider experience will be evaluated using multiple signals: `wait_time_minutes`, `cancelled_by_rider`, `completed`, `surge_multiplier`.

The dashboard will show the individual component metrics alongside the Experience Score. This prevents the composite score from hiding the individual signals that contribute to degraded experience.

## 9. User Stories

Each story follows Kalvium's required **Role + Action + Business Benefit** format.

**US-01** — As an Operations Manager, I want to compare rider experience across cities, so that I can identify cities requiring operational attention.

**US-02** — As an Operations Manager, I want to compare normal-demand and high-demand periods, so that I can understand when rider experience becomes worse.

**US-03** — As an Operations Manager, I want to see acceptance, cancellation, surge, supply, and wait-time metrics together, so that I can identify behaviours associated with poor rider experience.

**US-04** — As a Data Analyst, I want to filter results by city and time period, so that I can investigate specific operational patterns.

**US-05** — As a Data Analyst, I want to see cancellation reasons, so that I can identify the most common reasons for ride cancellations.

## 10. Product Scope

**In Scope — V1**
- City-level comparison
- High-demand analysis
- Driver acceptance analysis
- Driver-level acceptance analysis
- Rider cancellation analysis
- Driver cancellation analysis
- Surge pricing analysis
- Wait-time analysis
- Completion-rate analysis
- Demand and supply analysis
- Cancellation reason analysis
- Experience Score
- City Degradation Score
- Interactive dashboard
- Dashboard filters
- City-level drill-down
- Driver-level analysis excluding null `driver_id` records

**Out of Scope — V1**
- Ride booking
- Automatic surge-price changes
- Automatic driver interventions
- Individual rider recommendations
- Real-time ride dispatch
- Live data refresh
- Mobile application
- Predictive/ML forecasting
- Managing actual drivers or riders

The explicit v1 boundary follows Kalvium's scope requirement.

## 11. Data Workflow Architecture

The product follows five stages:

```
1. INGESTION
      ↓
2. CLEANING & VALIDATION
      ↓
3. SQL / PYTHON ANALYSIS
      ↓
4. VISUALISATION
      ↓
5. DELIVERY
```

**Stage 1 — Ingestion**

Load the project dataset into the analysis environment.

**Stage 2 — Cleaning & Validation**

Clean missing values and validate logical rules.

Validation assertions:
```
completed = true          → accepted = true
cancellation_reason set   → cancelled_by_rider = true OR cancelled_by_driver = true
surge_multiplier          → must be between 1.0 and 5.0
wait_time_minutes         → must be >= 0
city_hour_available_drivers → must be >= 0
city_hour_requested_rides   → must be >= 0
```

Invalid records will be logged and excluded from KPI calculations where the violation affects the metric.

**Stage 3 — SQL / Python Analysis**

Generate: city-level summaries, city-hour summaries, normal vs. high-demand comparisons, acceptance metrics, cancellation metrics, supply metrics, Experience Score, City Degradation Score, driver-level acceptance analysis.

**Stage 4 — Visualisation**

The Streamlit dashboard will display: KPI cards, city comparisons, high-demand vs. normal-demand comparisons, root-cause analysis, cancellation reasons.

**Stage 5 — Delivery**

The final analytical product will be delivered as a Streamlit dashboard for Operations Managers and Data Analysts.

This follows the Kalvium expectation that the workflow be mapped from ingestion through delivery.

## 12. Dashboard Requirements

**Dashboard Layout**

```
┌──────────────────────────────────────────────────────────┐
│                 ROADIES-CITYRIDE                          │
│              Rider Experience Dashboard                   │
├──────────────────────────────────────────────────────────┤
│ Total Requests │ Acceptance │ Cancellation │ Completion   │
│ Avg Wait Time  │ Avg Surge                                │
├──────────────────────────────────────────────────────────┤
│                 CITY COMPARISON                           │
│ City | Acceptance | Cancellation | Completion | Degrad.   │
├──────────────────────────────────────────────────────────┤
│            HIGH DEMAND vs NORMAL DEMAND                   │
│ Acceptance | Cancellation | Completion | Wait | Surge     │
├────────────────────────────┬──────────────────────────────┤
│ ROOT-CAUSE VIEW             │ CANCELLATION REASONS         │
│ Demand → Supply              │ Bar Chart                    │
│ → Acceptance → Wait         │                              │
│ → Cancellation → Completion │                              │
└────────────────────────────┴──────────────────────────────┘
```

**Sidebar Filters**
City, date range, hour, demand period, demand level, cancellation reason.

**Interaction Patterns**
- Clicking a city filters the other dashboard sections to that city.
- Sidebar filters apply globally across dashboard sections.
- Hover tooltips display exact metric values.
- A Reset Filters button clears all active filters.

## 13. Risk & Assumption Analysis

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Surge/cancellation correlation is mistaken for causation | Medium | Medium | Label findings as associations and show multiple signals |
| Experience Score hides individual signals | Medium | High | Display component metrics alongside the score |
| Null `driver_id` affects driver-level analysis | High | Low–Medium | Exclude null-driver records from driver-level metrics and document the limitation |
| Dataset violates logical rules | Low | High | Run validation assertions during cleaning |
| High-demand threshold changes if dataset changes | Low | Medium | Document the city-specific percentile calculation |
| `request_timestamp` timezone is unspecified in the data dictionary | Low | Medium — could shift hour-of-day bucketing and therefore `is_high_demand` results | Confirm timezone (e.g. IST) with the Data Owner before implementing hour-based derived fields |

**Key Assumptions**
- The dataset contains approximately 50,000–100,000 ride records.
- The analysis covers 90 days.
- The project contains 6 cities.
- Each record represents one ride request.
- High demand is determined using the city-specific 80th percentile.
- Driver-level analysis excludes null `driver_id` records.
- Correlation will not be presented as proof of causation.
- KPI thresholds are working thresholds and may change after validation.
- Experience Score methodology (placeholder formula in Section 5) will be finalized during analysis.
- City Degradation Score methodology (placeholder formula in Section 5) will be finalized during analysis.
- `request_timestamp` timezone is assumed to be IST pending confirmation (see risk table above).

Kalvium specifically recommends surfacing unconfirmed assumptions as risks rather than hiding them.

## 14. Data Quality & Validation Requirements

Before KPI calculations, required checks:
- `ride_id` uniqueness
- Missing-value checks
- Data-type validation
- Boolean field validation
- Timestamp validation
- Cancellation logic validation
- Completion/acceptance logic validation
- Surge range validation
- Wait-time range validation
- Demand/supply non-negative validation
- Null `driver_id` analysis

**Invalid Data Handling**

```
Invalid record
      ↓
Log validation failure
      ↓
Determine whether metric is affected
      ↓
Exclude affected record from relevant KPI
      ↓
Document impact
```

## 15. Final Success Criteria

The product is ready for final review when:
- All 8 business questions are answerable.
- All 6 cities can be compared.
- All 6 cities can be ranked using City Degradation Score.
- High-demand periods use the city-specific 80th-percentile rule.
- KPI calculations match validated Python/SQL results.
- Driver-level acceptance analysis works for valid `driver_id` records.
- Users can filter by city and time.
- City selection updates relevant dashboard sections.
- Cancellation reasons can be analysed.
- The 3 most degraded cities can be identified.
- Key behaviours associated with degradation can be surfaced.
- Dashboard results can be traced back to the underlying dataset.

## 16. Final Product Question

Which cities experience the biggest decline in rider experience during high-demand periods, and which operational behaviours are most associated with that decline?

*End of PRD*
