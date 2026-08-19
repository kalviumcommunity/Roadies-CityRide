-- Roadies-CityRide Business Metrics Queries
-- Core analytical metrics for the ride lifecycle

-- ============================================================
-- CORE METRICS
-- ============================================================

-- Overall business metrics
-- Source: rides table
-- Grain: Single row (global summary)
SELECT
    COUNT(*) AS total_rides,
    SUM(was_accepted) AS accepted_rides,
    SUM(ride_completed) AS completed_rides,
    SUM(rider_cancelled) AS rider_cancellations,
    SUM(driver_cancelled) AS driver_cancellations,
    ROUND(SUM(was_accepted) * 100.0 / COUNT(*), 2) AS acceptance_rate,
    ROUND(SUM(ride_completed) * 100.0 / COUNT(*), 2) AS completion_rate,
    ROUND(SUM(rider_cancelled) * 100.0 / COUNT(*), 2) AS rider_cancel_rate,
    ROUND(SUM(driver_cancelled) * 100.0 / COUNT(*), 2) AS driver_cancel_rate,
    ROUND(AVG(wait_time_minutes), 2) AS avg_wait_time,
    ROUND(AVG(surge_multiplier), 2) AS avg_surge,
    ROUND(AVG(demand_supply_ratio), 2) AS avg_demand_supply_ratio,
    ROUND(SUM(CASE WHEN is_high_demand = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS high_demand_share
FROM rides;


-- ============================================================
-- CITY-LEVEL METRICS
-- ============================================================

-- Metrics grouped by city
-- Source: rides table
-- Grain: One row per city
SELECT
    city,
    COUNT(*) AS ride_volume,
    ROUND(SUM(was_accepted) * 100.0 / COUNT(*), 2) AS acceptance_rate,
    ROUND(SUM(ride_completed) * 100.0 / COUNT(*), 2) AS completion_rate,
    ROUND(SUM(rider_cancelled) * 100.0 / COUNT(*), 2) AS rider_cancel_rate,
    ROUND(SUM(driver_cancelled) * 100.0 / COUNT(*), 2) AS driver_cancel_rate,
    ROUND(AVG(wait_time_minutes), 2) AS avg_wait_time,
    ROUND(AVG(surge_multiplier), 2) AS avg_surge,
    ROUND(AVG(demand_supply_ratio), 2) AS avg_demand_supply_ratio,
    ROUND(SUM(CASE WHEN is_high_demand = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS high_demand_share
FROM rides
GROUP BY city
ORDER BY ride_volume DESC;


-- ============================================================
-- DEMAND-PERIOD COMPARISON
-- ============================================================

-- Metrics comparing normal vs high demand
-- Source: rides table
-- Grain: One row per demand period
SELECT
    CASE WHEN is_high_demand = 1 THEN 'high' ELSE 'normal' END AS demand_period,
    COUNT(*) AS ride_count,
    ROUND(SUM(was_accepted) * 100.0 / COUNT(*), 2) AS acceptance_rate,
    ROUND(SUM(ride_completed) * 100.0 / COUNT(*), 2) AS completion_rate,
    ROUND(SUM(rider_cancelled) * 100.0 / COUNT(*), 2) AS rider_cancel_rate,
    ROUND(SUM(driver_cancelled) * 100.0 / COUNT(*), 2) AS driver_cancel_rate,
    ROUND(AVG(wait_time_minutes), 2) AS avg_wait_time,
    ROUND(AVG(surge_multiplier), 2) AS avg_surge,
    ROUND(AVG(demand_supply_ratio), 2) AS avg_demand_supply_ratio
FROM rides
GROUP BY is_high_demand
ORDER BY is_high_demand;


-- ============================================================
-- TIME-BASED METRICS
-- ============================================================

-- Daily metrics
-- Source: rides table
-- Grain: One row per day
SELECT
    DATE(request_timestamp) AS ride_date,
    COUNT(*) AS ride_count,
    ROUND(SUM(was_accepted) * 100.0 / COUNT(*), 2) AS acceptance_rate,
    ROUND(SUM(rider_cancelled) * 100.0 / COUNT(*), 2) AS rider_cancel_rate,
    ROUND(AVG(wait_time_minutes), 2) AS avg_wait_time,
    ROUND(AVG(surge_multiplier), 2) AS avg_surge
FROM rides
GROUP BY DATE(request_timestamp)
ORDER BY ride_date;


-- Hourly metrics
-- Source: rides table
-- Grain: One row per hour
SELECT
    STRFTIME('%H', request_timestamp) AS ride_hour,
    COUNT(*) AS ride_count,
    ROUND(SUM(was_accepted) * 100.0 / COUNT(*), 2) AS acceptance_rate,
    ROUND(SUM(rider_cancelled) * 100.0 / COUNT(*), 2) AS rider_cancel_rate,
    ROUND(AVG(wait_time_minutes), 2) AS avg_wait_time
FROM rides
GROUP BY STRFTIME('%H', request_timestamp)
ORDER BY ride_hour;


-- Day of week metrics
-- Source: rides table
-- Grain: One row per day of week
SELECT
    CASE CAST(STRFTIME('%w', request_timestamp) AS INTEGER)
        WHEN 0 THEN 'Sunday'
        WHEN 1 THEN 'Monday'
        WHEN 2 THEN 'Tuesday'
        WHEN 3 THEN 'Wednesday'
        WHEN 4 THEN 'Thursday'
        WHEN 5 THEN 'Friday'
        WHEN 6 THEN 'Saturday'
    END AS day_name,
    COUNT(*) AS ride_count,
    ROUND(SUM(was_accepted) * 100.0 / COUNT(*), 2) AS acceptance_rate,
    ROUND(SUM(rider_cancelled) * 100.0 / COUNT(*), 2) AS rider_cancel_rate,
    ROUND(AVG(wait_time_minutes), 2) AS avg_wait_time
FROM rides
GROUP BY STRFTIME('%w', request_timestamp)
ORDER BY STRFTIME('%w', request_timestamp);


-- ============================================================
-- HIGH-RISK CITY DETERIORATION METRICS
-- ============================================================

-- City-level deterioration: normal vs high demand
-- Source: rides table
-- Grain: One row per city with normal/high values and changes
WITH city_normal AS (
    SELECT
        city,
        COUNT(*) AS normal_rides,
        ROUND(SUM(was_accepted) * 100.0 / COUNT(*), 2) AS normal_acceptance,
        ROUND(SUM(ride_completed) * 100.0 / COUNT(*), 2) AS normal_completion,
        ROUND(SUM(rider_cancelled) * 100.0 / COUNT(*), 2) AS normal_cancel,
        ROUND(AVG(wait_time_minutes), 2) AS normal_wait,
        ROUND(AVG(surge_multiplier), 2) AS normal_surge
    FROM rides
    WHERE is_high_demand = 0
    GROUP BY city
),
city_high AS (
    SELECT
        city,
        COUNT(*) AS high_rides,
        ROUND(SUM(was_accepted) * 100.0 / COUNT(*), 2) AS high_acceptance,
        ROUND(SUM(ride_completed) * 100.0 / COUNT(*), 2) AS high_completion,
        ROUND(SUM(rider_cancelled) * 100.0 / COUNT(*), 2) AS high_cancel,
        ROUND(AVG(wait_time_minutes), 2) AS high_wait,
        ROUND(AVG(surge_multiplier), 2) AS high_surge
    FROM rides
    WHERE is_high_demand = 1
    GROUP BY city
)
SELECT
    n.city,
    n.normal_rides,
    h.high_rides,
    n.normal_acceptance,
    h.high_acceptance,
    ROUND(h.high_acceptance - n.normal_acceptance, 2) AS acceptance_change,
    n.normal_completion,
    h.high_completion,
    ROUND(h.high_completion - n.normal_completion, 2) AS completion_change,
    n.normal_cancel,
    h.high_cancel,
    ROUND(h.high_cancel - n.normal_cancel, 2) AS cancel_change,
    n.normal_wait,
    h.high_wait,
    ROUND(h.high_wait - n.normal_wait, 2) AS wait_change,
    n.normal_surge,
    h.high_surge,
    ROUND(h.high_surge - n.normal_surge, 2) AS surge_change
FROM city_normal n
JOIN city_high h ON n.city = h.city
ORDER BY cancel_change DESC;
