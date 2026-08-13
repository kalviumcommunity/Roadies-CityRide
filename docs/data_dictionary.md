# Roadies-CityRide Data Dictionary

> Defines the synthetic ride-sharing dataset required for the analysis of city-level behaviours that degrade rider experience during high-demand periods.

## Dataset Overview

| Property | Value |
|---|---|
| **Grain** | One row per ride request |
| **Format** | Single denormalised CSV/JSON table |
| **Approximate size** | 50,000–100,000 rows (90 days, 6 cities) |
| **Time range** | 90 consecutive days |
| **Entities** | Rides (primary), with city-hour context denormalised |

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
| **Generated directly** | ride_id, rider_id, driver_id, city, request_timestamp, accepted, cancelled_by_rider, cancelled_by_driver, cancellation_reason, driver_acceptance_rate, driver_rating, city_hour_requested_rides, city_hour_available_drivers, surge_multiplier, base_fare, wait_time_minutes, trip_duration_minutes, trip_distance_km |
| **Derived in feature engineering** | date, hour, day_of_week, is_weekend, demand_level, supply_ratio, estimated_fare, is_high_demand, experience_score |

### 5. High-Demand Classification

High-demand periods are identified from the raw data by:

1. Computing `city_hour_requested_rides` per city per hour.
2. Computing demand percentile ranks within each city.
3. Classifying hours above the 80th percentile as high-demand.

This is **not** encoded in the raw data. It will be derived in feature engineering (Issue #30), keeping the analysis discoverable rather than predetermined.

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

| Field | Type | Required | Description | Example | Valid Range |
|---|---|---|---|---|---|
| `ride_id` | string | Yes | Unique ride request identifier | `"R-000001"` | Non-empty, unique |
| `rider_id` | string | Yes | Unique rider identifier | `"RDR-1042"` | Non-empty |
| `driver_id` | string | No | Assigned driver identifier (null if no driver assigned) | `"DRV-0238"` | Non-empty or null |

### Temporal

| Field | Type | Required | Description | Example | Valid Range |
|---|---|---|---|---|---|
| `request_timestamp` | datetime (ISO 8601) | Yes | Date and time of ride request | `"2025-07-15T08:32:00"` | 2025-07-01 to 2025-09-28 |

### Location

| Field | Type | Required | Description | Example | Valid Values |
|---|---|---|---|---|---|
| `city` | string | Yes | City where the ride was requested | `"Mumbai"` | `Mumbai`, `Delhi`, `Bangalore`, `Hyderabad`, `Chennai`, `Pune` |

### Ride Outcome

| Field | Type | Required | Description | Example | Valid Values |
|---|---|---|---|---|---|
| `accepted` | boolean | Yes | Whether a driver accepted the ride request | `true` | `true`, `false` |
| `completed` | boolean | Yes | Whether the ride was completed | `true` | `true`, `false` |
| `cancelled_by_rider` | boolean | Yes | Whether the rider cancelled | `false` | `true`, `false` |
| `cancelled_by_driver` | boolean | Yes | Whether the driver cancelled after acceptance | `false` | `true`, `false` |
| `cancellation_reason` | string | No | Reason for cancellation (null if not cancelled) | `"Long wait time"` | `Long wait time`, `Driver rude`, `Changed mind`, `Vehicle quality`, `Other`, null |

### Driver Behaviour

| Field | Type | Required | Description | Example | Valid Range |
|---|---|---|---|---|---|
| `driver_acceptance_rate` | float | Yes | Historical acceptance rate of the assigned driver (0.0–1.0). Null if no driver assigned. | `0.82` | 0.0–1.0 or null |
| `driver_rating` | float | No | Driver's average rating (1.0–5.0). Null if no driver assigned. | `4.3` | 1.0–5.0 or null |

### Demand and Supply (City-Hour Context)

| Field | Type | Required | Description | Example | Valid Range |
|---|---|---|---|---|---|
| `city_hour_requested_rides` | integer | Yes | Total ride requests in this city during this hour | `142` | 1–500 |
| `city_hour_available_drivers` | integer | Yes | Total available drivers in this city during this hour | `38` | 0–300 |
| `demand_level` | string | Yes | Categorical demand level based on requested rides | `"high"` | `low`, `medium`, `high`, `critical` |

### Surge Pricing

| Field | Type | Required | Description | Example | Valid Range |
|---|---|---|---|---|---|
| `surge_multiplier` | float | Yes | Current surge pricing multiplier | `1.8` | 1.0–5.0 |
| `base_fare` | float | Yes | Base fare before surge (in INR) | `120.00` | 50.0–500.0 |

### Rider Experience (Ride-Level Outcomes)

| Field | Type | Required | Description | Example | Valid Range |
|---|---|---|---|---|---|
| `wait_time_minutes` | float | Yes | Minutes from request to driver arrival (null if not accepted) | `7.2` | 0.0–60.0 or null |
| `trip_duration_minutes` | float | No | Actual trip duration in minutes (null if not completed) | `22.5` | 0.0–120.0 or null |
| `trip_distance_km` | float | No | Trip distance in kilometres (null if not completed) | `8.3` | 0.0–50.0 or null |

---

## Derived Fields (Feature Engineering)

These fields are **not** in the raw dataset. They are computed later.

| Field | Type | Source | Description |
|---|---|---|---|
| `date` | date | `request_timestamp` | Date portion of the timestamp |
| `hour` | integer | `request_timestamp` | Hour of day (0–23) |
| `day_of_week` | string | `request_timestamp` | Day name (`Monday`–`Sunday`) |
| `is_weekend` | boolean | `day_of_week` | `true` if Saturday or Sunday |
| `supply_ratio` | float | `city_hour_available_drivers / city_hour_requested_rides` | Drivers per request |
| `estimated_fare` | float | `base_fare * surge_multiplier` | Estimated fare with surge |
| `is_high_demand` | boolean | Demand percentile ranking | `true` if city-hour demand is above 80th percentile |
| `experience_score` | float | Weighted combination of wait time, completion, cancellation | Composite rider experience metric (0.0–1.0) |

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
| `driver_acceptance_rate` is null when `driver_id` is null | No driver metrics without a driver |

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
