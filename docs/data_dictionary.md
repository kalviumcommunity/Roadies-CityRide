# Roadies-CityRide Data Dictionary

> Authoritative reference for the synthetic ride-sharing dataset. Defines every field, its business meaning, and how it maps to the core problem: **Which city-level behaviours consistently degrade rider experience during high-demand periods?**

## Dataset Overview

| Property | Value |
|---|---|
| **Grain** | One row per ride request |
| **Format** | Single denormalised CSV/JSON table |
| **Approximate size** | 50,000–100,000 rows (90 days, 6 cities) |
| **Time range** | 90 consecutive days (2025-07-01 to 2025-09-28) |
| **Entities** | Rides (primary), with city-hour context denormalised |
| **Primary key** | `ride_id` |

---

## Business Definitions

The following terms are used consistently throughout the project. Two analysts applying these definitions should arrive at the same metric values.

| Term | Definition |
|---|---|
| **Ride request** | A single rider interaction initiating a trip. One row in the dataset. |
| **Accepted ride** | A ride request where a driver has agreed to pick up the rider (`accepted = true`). |
| **Completed ride** | A ride that was accepted and the trip finished successfully (`completed = true`). Always implies acceptance. |
| **Rider cancellation** | The rider cancels before the trip completes (`cancelled_by_rider = true`). May occur before or after acceptance. |
| **Driver cancellation** | The driver cancels after accepting the ride (`cancelled_by_driver = true`). Only possible if the ride was accepted. |
| **Demand** | The number of ride requests in a city during a specific hour (`city_hour_requested_rides`). |
| **Supply** | The number of available drivers in a city during a specific hour (`city_hour_available_drivers`). |
| **Surge pricing** | Dynamic pricing multiplier applied to the base fare during periods of high demand or low supply. |
| **High-demand period** | A city-hour where demand exceeds the 80th percentile of demand within that city. Derived later (Issue #30). |
| **Rider experience degradation** | Measurable deterioration in rider-facing outcomes (longer wait times, higher cancellation rates, lower completion rates, higher surge). Not a single field — measured through multiple signals. |

---

## Design Decisions

### 1. Grain

Each row represents one ride request. This is the most natural grain because:

- It allows direct analysis of ride-level outcomes (accepted, cancelled, completed).
- City-level and time-based aggregations can be derived via GROUP BY.
- SQL and Python analysis can work directly with this table.
- It captures the full lifecycle of a single rider interaction.

### 2. Entity Model

A single denormalised table is used rather than multiple normalised tables. Reasons:

- Simpler for CSV/JSON ingestion and later SQL analysis.
- Avoids JOIN complexity for a portfolio project.
- City-hour demand/supply context is denormalised into each ride row (same values for all rides in the same city-hour).
- Driver historical attributes are denormalised into each ride row.

### 3. Keys

| Key | Field | Purpose |
|---|---|---|
| Primary key | `ride_id` | Unique identifier for each ride request |
| Logical foreign key | `rider_id` | Identifies the rider (denormalised) |
| Logical foreign key | `driver_id` | Identifies the assigned driver (null if unassigned) |
| Logical grouping | `city` + `request_hour` | Identifies the city-hour context |

### 4. Raw vs. Derived Fields

| Category | Fields |
|---|---|
| **Generated directly (raw)** | `ride_id`, `rider_id`, `driver_id`, `city`, `request_timestamp`, `accepted`, `completed`, `cancelled_by_rider`, `cancelled_by_driver`, `cancellation_reason`, `driver_acceptance_rate`, `driver_rating`, `city_hour_requested_rides`, `city_hour_available_drivers`, `demand_level`, `surge_multiplier`, `base_fare`, `wait_time_minutes`, `trip_duration_minutes`, `trip_distance_km` |
| **Derived in feature engineering** | `date`, `hour`, `day_of_week`, `is_weekend`, `supply_ratio`, `estimated_fare`, `is_high_demand`, `experience_score` |

> **Note:** `demand_level` is generated directly by the synthetic generator as a categorical label (low/medium/high/critical) based on the request count in each city-hour. It is not derived later.

### 5. High-Demand Classification

High-demand periods are identified from the raw data by:

1. Computing `city_hour_requested_rides` per city per hour.
2. Computing demand percentile ranks within each city.
3. Classifying hours above the 80th percentile as high-demand.

This is **not** encoded in the raw data as a boolean. It will be derived in feature engineering (Issue #30), keeping the analysis discoverable rather than predetermined.

### 6. Rider Experience Degradation

Rider experience is measured through multiple independent signals:

- `wait_time_minutes` — longer waits indicate worse experience.
- `cancelled_by_rider` — cancellation indicates dissatisfaction.
- `completed` — failure to complete indicates poor experience.
- `surge_multiplier` — high surge may indicate constrained supply.

No single field "scores" experience. The later analysis will construct composite metrics, preventing artificial conclusions.

### 7. City-Level Comparison

City-level comparisons are supported by:

- `city` field present in every row.
- City-hour aggregates (`city_hour_requested_rides`, `city_hour_available_drivers`) enable demand/supply comparison.
- All ride-level outcomes can be aggregated by city.

---

## Field Definitions

### Identifiers

| Field | Type | Required | Nullable | Raw/Derived | Unit | Valid Range | Business Meaning | Technical Meaning | Analytical Role | Example |
|---|---|---|---|---|---|---|---|---|---|---|
| `ride_id` | string | Yes | No | Raw | — | Non-empty, unique | Unique identifier for each ride request | Primary key, format `R-NNNNNN` | Join key, deduplication, counting | `"R-000001"` |
| `rider_id` | string | Yes | No | Raw | — | Non-empty | Identifies the rider who made the request | Foreign key, format `RDR-NNNN` | Rider-level segmentation | `"RDR-1042"` |
| `driver_id` | string | No | Yes | Raw | — | Non-empty or null | Identifies the assigned driver (null if unassigned) | Foreign key, format `DRV-NNNN` | Driver-level analysis | `"DRV-0238"` |

### Temporal

| Field | Type | Required | Nullable | Raw/Derived | Unit | Valid Range | Business Meaning | Technical Meaning | Analytical Role | Example |
|---|---|---|---|---|---|---|---|---|---|---|
| `request_timestamp` | datetime (ISO 8601) | Yes | No | Raw | — | 2025-07-01 to 2025-09-28 | Date and time of ride request | ISO 8601 string, e.g. `2025-07-15T08:32:00` | Time-based analysis, hour/day extraction | `"2025-07-15T08:32:00"` |

### Location

| Field | Type | Required | Nullable | Raw/Derived | Unit | Valid Values | Business Meaning | Technical Meaning | Analytical Role | Example |
|---|---|---|---|---|---|---|---|---|---|---|
| `city` | string | Yes | No | Raw | — | `Mumbai`, `Delhi`, `Bangalore`, `Hyderabad`, `Chennai`, `Pune` | City where the ride was requested | Categorical, 6 levels | City comparison, segmentation | `"Mumbai"` |

### Ride Outcome

| Field | Type | Required | Nullable | Raw/Derived | Unit | Valid Values | Business Meaning | Technical Meaning | Analytical Role | Example |
|---|---|---|---|---|---|---|---|---|---|---|
| `accepted` | boolean | Yes | No | Raw | — | `true`, `false` | Whether a driver accepted the ride request | Boolean flag | Funnel analysis (acceptance rate) | `true` |
| `completed` | boolean | Yes | No | Raw | — | `true`, `false` | Whether the ride was completed end-to-end | Boolean flag, implies `accepted` | Funnel analysis (completion rate), experience signal | `true` |
| `cancelled_by_rider` | boolean | Yes | No | Raw | — | `true`, `false` | Whether the rider cancelled the request | Boolean flag, implies not `completed` | Rider dissatisfaction signal | `false` |
| `cancelled_by_driver` | boolean | Yes | No | Raw | — | `true`, `false` | Whether the driver cancelled after acceptance | Boolean flag, implies `accepted` | Driver behaviour analysis | `false` |
| `cancellation_reason` | string | No | Yes | Raw | — | `Long wait time`, `Driver rude`, `Changed mind`, `Vehicle quality`, `Other`, null | Reason for cancellation (null if not cancelled) | Categorical, null when neither party cancelled | Root-cause analysis of cancellations | `"Long wait time"` |

### Driver Behaviour

| Field | Type | Required | Nullable | Raw/Derived | Unit | Valid Range | Business Meaning | Technical Meaning | Analytical Role | Example |
|---|---|---|---|---|---|---|---|---|---|---|
| `driver_acceptance_rate` | float | Yes | Yes | Raw | ratio | 0.0–1.0 or null | Historical acceptance rate of the assigned driver | Float, null if no driver assigned | Driver quality signal, acceptance behaviour analysis | `0.82` |
| `driver_rating` | float | No | Yes | Raw | stars | 1.0–5.0 or null | Driver's average rating from past riders | Float, null if no driver assigned | Driver quality proxy | `4.3` |

### Demand and Supply (City-Hour Context)

| Field | Type | Required | Nullable | Raw/Derived | Unit | Valid Range | Business Meaning | Technical Meaning | Analytical Role | Example |
|---|---|---|---|---|---|---|---|---|---|---|
| `city_hour_requested_rides` | integer | Yes | No | Raw | rides/hour | 1–500 | Total ride requests in this city during this hour | Denormalised city-hour aggregate | Demand measurement | `142` |
| `city_hour_available_drivers` | integer | Yes | No | Raw | drivers/hour | 0–300 | Total available drivers in this city during this hour | Denormalised city-hour aggregate | Supply measurement | `38` |
| `demand_level` | string | Yes | No | Raw | — | `low`, `medium`, `high`, `critical` | Categorical demand level based on requested rides | Generated by synthetic generator | Quick demand segmentation | `"high"` |

### Surge Pricing

| Field | Type | Required | Nullable | Raw/Derived | Unit | Valid Range | Business Meaning | Technical Meaning | Analytical Role | Example |
|---|---|---|---|---|---|---|---|---|---|---|
| `surge_multiplier` | float | Yes | No | Raw | multiplier | 1.0–5.0 | Current surge pricing multiplier applied to fare | Float, 1.0 = no surge | Pricing pressure measurement | `1.8` |
| `base_fare` | float | Yes | No | Raw | INR | 50.0–500.0 | Base fare before surge is applied | Float, currency in INR | Fare baseline | `120.00` |

### Rider Experience (Ride-Level Outcomes)

| Field | Type | Required | Nullable | Raw/Derived | Unit | Valid Range | Business Meaning | Technical Meaning | Analytical Role | Example |
|---|---|---|---|---|---|---|---|---|---|---|
| `wait_time_minutes` | float | Yes | Yes | Raw | minutes | 0.0–60.0 or null | Minutes from request to driver arrival (null if not accepted) | Float, null when `accepted = false` | Rider experience degradation signal | `7.2` |
| `trip_duration_minutes` | float | No | Yes | Raw | minutes | 0.0–120.0 or null | Actual trip duration in minutes (null if not completed) | Float, null when `completed = false` | Trip characteristics | `22.5` |
| `trip_distance_km` | float | No | Yes | Raw | km | 0.0–50.0 or null | Trip distance in kilometres (null if not completed) | Float, null when `completed = false` | Trip characteristics | `8.3` |

---

## Derived Fields (Feature Engineering)

These fields are **not** in the raw dataset. They are computed later.

| Field | Type | Source | Unit | Description | Analytical Role |
|---|---|---|---|---|---|
| `date` | date | `request_timestamp` | — | Date portion of the timestamp | Daily aggregation |
| `hour` | integer | `request_timestamp` | hour (0–23) | Hour of day | Hourly pattern analysis |
| `day_of_week` | string | `request_timestamp` | — | Day name (`Monday`–`Sunday`) | Weekly pattern analysis |
| `is_weekend` | boolean | `day_of_week` | — | `true` if Saturday or Sunday | Weekend vs weekday comparison |
| `supply_ratio` | float | `city_hour_available_drivers / city_hour_requested_rides` | drivers/request | Drivers per request | Supply-demand balance metric |
| `demand_supply_ratio` | float | `city_hour_requested_rides / city_hour_available_drivers` | rides/driver | Rides per available driver | Demand pressure metric |
| `supply_pressure` | float | `city_hour_available_drivers / city_hour_requested_rides` | drivers/driver | Drivers per requested ride | Supply availability metric |
| `demand_intensity` | float | `requested / (requested + available)` | proportion (0–1) | Demand share of total | Normalized demand measure |
| `driver_availability_rate` | float | `available / (requested + available)` | proportion (0–1) | Supply share of total | Normalized supply measure |
| `demand_surplus` | float | `requested - available` | count | Excess demand over supply | Shortage indicator |
| `surge_pressure` | float | `max(0, surplus / requested)` | proportion (0–1) | Normalized demand surplus | Surge likelihood indicator |
| `surge_deviation` | float | `surge_multiplier - 1.0` | multiplier units | Deviation from no-surge baseline | Surge level measure |
| `surge_intensity` | float | `(surge_multiplier - 1.0) / 4.0` | proportion (0–1) | Normalized surge (0=no surge, 1=max) | Surge level measure |
| `surge_category` | string | categorical band | category | no_surge, low, moderate, high | Surge segmentation |
| `has_surge` | boolean | `surge_multiplier > 1.0` | boolean | Whether surge pricing is active | Surge flag |
| `surge_to_demand_ratio` | float | `surge_multiplier / demand_supply_ratio` | ratio | Surge relative to demand pressure | Combined metric |
| `was_accepted` | boolean | `accepted == true` | boolean | Whether this ride was accepted | Acceptance flag |
| `was_not_accepted` | boolean | `accepted == false` | boolean | Whether this ride was NOT accepted | Rejection flag |
| `acceptance_rate_deviation` | float | `driver_acceptance_rate - 0.80` | proportion (-1 to 1) | Deviation from baseline acceptance rate | Driver behaviour metric |
| `acceptance_rate_band` | string | categorical band | category | well_above, above, near_baseline, below, well_below | Acceptance rate segmentation |
| `has_driver` | boolean | `driver_id is not null` | boolean | Whether a driver was assigned | Driver assignment flag |
| `estimated_fare` | float | `base_fare * surge_multiplier` | INR | Estimated fare with surge applied | Fare analysis |
| `is_high_demand` | boolean | Demand percentile ranking | — | `true` if city-hour demand is above 80th percentile | High-demand period classification |
| `experience_score` | float | Weighted combination of wait time, completion, cancellation | 0.0–1.0 | Composite rider experience metric | Overall experience measurement |

---

## Business Context Mapping

The core problem is: **Which city-level behaviours consistently degrade rider experience during high-demand periods?**

The following table maps each business concept to the relevant fields and explains their purpose.

| Business Concept | Relevant Fields | Purpose |
|---|---|---|
| **Demand measurement** | `city_hour_requested_rides`, `demand_level`, `city`, `request_timestamp` | Determine demand intensity per city-hour |
| **Supply measurement** | `city_hour_available_drivers`, `city`, `request_timestamp` | Measure driver availability per city-hour |
| **Driver acceptance behaviour** | `accepted`, `driver_acceptance_rate`, `driver_id`, `city`, `demand_level` | Measure whether drivers accept rides and how demand affects acceptance |
| **Rider cancellation behaviour** | `cancelled_by_rider`, `cancellation_reason`, `city`, `demand_level`, `surge_multiplier` | Measure rider-side drop-off and its causes |
| **Driver cancellation behaviour** | `cancelled_by_driver`, `cancellation_reason`, `driver_id`, `city` | Measure driver-side drop-off after acceptance |
| **Surge pricing** | `surge_multiplier`, `base_fare`, `city`, `demand_level` | Measure pricing pressure during high demand |
| **Waiting / rider experience** | `wait_time_minutes`, `completed`, `cancelled_by_rider`, `city` | Measure degradation in rider-facing outcomes |
| **City comparison** | `city`, all outcome fields | Compare operational behaviour across 6 cities |
| **Time-based analysis** | `request_timestamp`, `city`, all outcome fields | Identify temporal patterns in experience degradation |
| **High-demand classification** | `is_high_demand` (derived), `city_hour_requested_rides` | Classify periods where demand exceeds normal levels |

---

## Derived Metrics

The following analytical metrics will be calculated during feature engineering and analysis. They are not stored in the raw dataset.

| Metric | Formula | Purpose |
|---|---|---|
| **Acceptance rate** | `count(accepted=true) / count(*)` per city-hour | Measure driver responsiveness |
| **Rider cancellation rate** | `count(cancelled_by_rider=true) / count(*)` per city-hour | Measure rider dissatisfaction |
| **Completion rate** | `count(completed=true) / count(*)` per city-hour | Measure ride fulfilment |
| **Supply ratio** | `city_hour_available_drivers / city_hour_requested_rides` | Measure supply-demand balance |
| **High-demand classification** | `demand_percentile > 0.80` within each city | Identify peak demand periods |
| **City-level degradation score** | Weighted combination of wait time, cancellation, completion across demand levels | Compare how much each city degrades during high demand |
| **Estimated fare** | `base_fare * surge_multiplier` | Total fare charged to rider |
| **Experience score** | Composite of wait time, completion, cancellation signals | Single measure of rider experience quality |

---

## Relationships and Constraints

### Logical Constraints

| Rule | Description |
|---|---|
| `completed` implies `accepted` | A ride cannot complete without acceptance |
| `cancelled_by_rider` implies not `completed` | A cancelled ride does not complete |
| `cancelled_by_driver` implies `accepted` | Only accepted rides can be driver-cancelled |
| `cancellation_reason` is null when not cancelled | Only present when `cancelled_by_rider` or `cancelled_by_driver` is true |
| `wait_time_minutes` is null when not accepted | No wait time if no driver was assigned |
| `trip_duration_minutes` is null when not completed | No trip duration if ride did not complete |
| `trip_distance_km` is null when not completed | No trip distance if ride did not complete |
| `driver_acceptance_rate` is null when `driver_id` is null | No driver metrics without a driver |
| `driver_rating` is null when `driver_id` is null | No driver metrics without a driver |

### City-Hour Grouping

All rides in the same city and hour share the same values for:
- `city_hour_requested_rides`
- `city_hour_available_drivers`
- `demand_level`

This denormalised context allows city-hour aggregation without JOINs.

---

## Example Rows

```
ride_id,rider_id,driver_id,request_timestamp,city,accepted,completed,cancelled_by_rider,cancelled_by_driver,cancellation_reason,driver_acceptance_rate,driver_rating,city_hour_requested_rides,city_hour_available_drivers,demand_level,surge_multiplier,base_fare,wait_time_minutes,trip_duration_minutes,trip_distance_km
R-000001,RDR-1042,DRV-0238,2025-07-15T08:32:00,Mumbai,true,true,false,false,null,0.82,4.3,142,38,high,1.8,120.00,7.2,22.5,8.3
R-000002,RDR-0087,null,2025-07-15T08:33:00,Mumbai,false,false,false,false,null,null,null,142,38,high,2.1,120.00,null,null,null
R-000003,RDR-2156,DRV-0091,2025-07-15T08:35:00,Delhi,true,false,false,true,Vehicle quality,0.91,4.7,87,52,medium,1.0,95.00,3.1,null,null
```

---

## Mapping to Business Questions

| Business Question | Supporting Fields |
|---|---|
| Which cities have the worst rider experience? | `city`, `wait_time_minutes`, `completed`, `cancelled_by_rider` |
| How does demand affect driver acceptance? | `city_hour_requested_rides`, `demand_level`, `accepted`, `driver_acceptance_rate` |
| Does surge pricing correlate with cancellations? | `surge_multiplier`, `cancelled_by_rider`, `cancellation_reason` |
| What happens to experience during high demand? | `is_high_demand` (derived), `wait_time_minutes`, `completed`, `surge_multiplier` |
| Which cities degrade most during high demand? | `city`, `is_high_demand` (derived), all experience fields |
| What is the relationship between supply and experience? | `city_hour_available_drivers`, `supply_ratio` (derived), `wait_time_minutes` |
| Are some drivers consistently low-acceptance? | `driver_id`, `driver_acceptance_rate` |
| What are the most common cancellation reasons? | `cancellation_reason`, `cancelled_by_rider`, `cancelled_by_driver` |

---

## Storage Format

| Stage | Format | Location |
|---|---|---|
| Raw generated | CSV | `data/raw/rides.csv` |
| Raw generated | CSV | `data/raw/city_hour.csv` (reference) |
| Processed | CSV or Parquet | `data/processed/` |
| SQLite | `.db` file | `data/roadies.db` |

The primary analytical dataset is the ride-level CSV. A separate city-hour reference table may be generated for convenience but is not required since city-hour context is already denormalised in the ride table.
