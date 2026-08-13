# Roadies-CityRide Dataset Profile

> Auto-generated profiling report. Describes the structure and quality of the ride-sharing dataset.

## Dataset Overview

| Metric | Value |
|---|---|
| Total rows | 50,000 |
| Total columns | 20 |
| Duplicate rows | 0 |
| Unique ride IDs | 50,000 |
| Cities | 6 |
| Riders | 50,000 |
| Drivers | 499 |
| Time range | 2025-07-01 00:05:00 to 2025-09-28 00:50:15 |
| Total missing values | 239,687 |
| Rows with missing values | 100.0% |

## Rides by City

| City | Count |
|---|---|
| Bangalore | 9,351 |
| Chennai | 6,904 |
| Delhi | 9,907 |
| Hyderabad | 7,501 |
| Mumbai | 10,626 |
| Pune | 5,711 |

## Rides by Demand Level

| Demand Level | Count |
|---|---|
| critical | 16,422 |
| high | 20,417 |
| low | 2,750 |
| medium | 10,411 |

## Rides by Outcome

| Outcome | Count |
|---|---|
| accepted | 17,484 |
| cancelled_by_driver | 354 |
| cancelled_by_rider | 1,161 |
| completed | 15,969 |
| not_accepted | 32,516 |
| not_completed | 34,031 |

## Key Rates

- Acceptance rate: 35.0%
- Completion rate: 31.9%
- Rider cancellation rate: 2.3%
- Driver cancellation rate: 0.7%

## Surge Pricing

| Stat | Value |
|---|---|
| Min | 1.00 |
| Max | 5.00 |
| Mean | 1.39 |
| Median | 1.37 |

## Wait Time

| Stat | Value (min) |
|---|---|
| Min | 0.50 |
| Max | 60.00 |
| Mean | 8.91 |
| Median | 6.15 |
| P95 | 26.95 |

## Column Profiles

| Column | Dtype | Non-Null | Null % | Unique | Unique % |
|---|---|---|---|---|---|
| ride_id | str | 50,000 | 0.0% | 50,000 | 100.0% |
| rider_id | str | 50,000 | 0.0% | 50,000 | 100.0% |
| driver_id | str | 24,408 | 51.2% | 499 | 1.0% |
| request_timestamp | str | 50,000 | 0.0% | 49,784 | 99.6% |
| city | str | 50,000 | 0.0% | 6 | 0.0% |
| accepted | bool | 50,000 | 0.0% | 2 | 0.0% |
| completed | bool | 50,000 | 0.0% | 2 | 0.0% |
| cancelled_by_rider | bool | 50,000 | 0.0% | 2 | 0.0% |
| cancelled_by_driver | bool | 50,000 | 0.0% | 2 | 0.0% |
| cancellation_reason | str | 1,515 | 97.0% | 5 | 0.0% |
| driver_acceptance_rate | float64 | 17,484 | 65.0% | 16,913 | 33.8% |
| driver_rating | float64 | 17,484 | 65.0% | 17,335 | 34.7% |
| city_hour_requested_rides | int64 | 50,000 | 0.0% | 208 | 0.4% |
| city_hour_available_drivers | int64 | 50,000 | 0.0% | 120 | 0.2% |
| demand_level | str | 50,000 | 0.0% | 4 | 0.0% |
| surge_multiplier | float64 | 50,000 | 0.0% | 48,531 | 97.1% |
| base_fare | float64 | 50,000 | 0.0% | 49,999 | 100.0% |
| wait_time_minutes | float64 | 17,484 | 65.0% | 16,538 | 33.1% |
| trip_duration_minutes | float64 | 15,969 | 68.1% | 15,715 | 31.4% |
| trip_distance_km | float64 | 15,969 | 68.1% | 14,962 | 29.9% |

## Numeric Column Statistics

| Column | Min | Max | Mean | Median | Std | P25 | P75 | P95 |
|---|---|---|---|---|---|---|---|---|
| driver_acceptance_rate | 0.42 | 1.00 | 0.81 | 0.81 | 0.10 | 0.74 | 0.88 | 0.98 |
| driver_rating | 3.10 | 5.00 | 4.23 | 4.24 | 0.32 | 4.02 | 4.45 | 4.77 |
| city_hour_requested_rides | 3.00 | 215.00 | 99.54 | 97.00 | 43.88 | 68.00 | 133.00 | 174.00 |
| city_hour_available_drivers | 0.00 | 123.00 | 48.70 | 48.00 | 23.21 | 31.00 | 66.00 | 88.00 |
| surge_multiplier | 1.00 | 5.00 | 1.39 | 1.37 | 0.23 | 1.23 | 1.52 | 1.76 |
| base_fare | 50.00 | 166.35 | 104.37 | 102.04 | 18.30 | 90.84 | 116.98 | 137.10 |
| wait_time_minutes | 0.50 | 60.00 | 8.91 | 6.15 | 8.88 | 2.51 | 12.35 | 26.95 |
| trip_duration_minutes | 1.00 | 120.00 | 19.90 | 13.38 | 20.19 | 5.53 | 27.50 | 60.54 |
| trip_distance_km | 0.50 | 50.00 | 7.97 | 5.50 | 7.87 | 2.29 | 11.09 | 23.80 |

## Categorical Column Top Values

### ride_id

| Value | Count |
|---|---|
| R-000001 | 1 |
| R-000002 | 1 |
| R-000003 | 1 |
| R-000004 | 1 |
| R-000005 | 1 |

### rider_id

| Value | Count |
|---|---|
| RDR-000001 | 1 |
| RDR-000002 | 1 |
| RDR-000003 | 1 |
| RDR-000004 | 1 |
| RDR-000005 | 1 |

### driver_id

| Value | Count |
|---|---|
| DRV-000427 | 71 |
| DRV-000338 | 68 |
| DRV-000373 | 67 |
| DRV-000184 | 66 |
| DRV-000278 | 66 |

### request_timestamp

| Value | Count |
|---|---|
| 2025-07-17 11:10:15 | 3 |
| 2025-07-02 07:28:21 | 2 |
| 2025-07-02 13:58:27 | 2 |
| 2025-07-02 21:08:40 | 2 |
| 2025-07-03 01:42:44 | 2 |

### city

| Value | Count |
|---|---|
| Mumbai | 10,626 |
| Delhi | 9,907 |
| Bangalore | 9,351 |
| Hyderabad | 7,501 |
| Chennai | 6,904 |

### accepted

| Value | Count |
|---|---|
| False | 32,516 |
| True | 17,484 |

### completed

| Value | Count |
|---|---|
| False | 34,031 |
| True | 15,969 |

### cancelled_by_rider

| Value | Count |
|---|---|
| False | 48,839 |
| True | 1,161 |

### cancelled_by_driver

| Value | Count |
|---|---|
| False | 49,646 |
| True | 354 |

### cancellation_reason

| Value | Count |
|---|---|
| Other | 384 |
| Long wait time | 332 |
| Vehicle quality | 319 |
| Changed mind | 309 |
| Driver rude | 171 |

### demand_level

| Value | Count |
|---|---|
| high | 20,417 |
| critical | 16,422 |
| medium | 10,411 |
| low | 2,750 |

