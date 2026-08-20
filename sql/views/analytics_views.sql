-- Roadies-CityRide Reusable SQL Views
-- Focused analytical views for dashboard/reporting

-- ============================================================
-- CITY-LEVEL PERFORMANCE VIEW
-- ============================================================

-- Grain: One row per city
-- Purpose: Core city-level metrics for reporting
CREATE VIEW IF NOT EXISTS vw_city_performance AS
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
GROUP BY city;


-- ============================================================
-- HIGH-DEMAND CITY PERFORMANCE VIEW
-- ============================================================

-- Grain: One row per city per demand period
-- Purpose: Compare normal vs high demand by city
CREATE VIEW IF NOT EXISTS vw_city_demand_comparison AS
SELECT
    city,
    CASE WHEN is_high_demand = 1 THEN 'high' ELSE 'normal' END AS demand_period,
    COUNT(*) AS ride_count,
    ROUND(SUM(was_accepted) * 100.0 / COUNT(*), 2) AS acceptance_rate,
    ROUND(SUM(ride_completed) * 100.0 / COUNT(*), 2) AS completion_rate,
    ROUND(SUM(rider_cancelled) * 100.0 / COUNT(*), 2) AS rider_cancel_rate,
    ROUND(AVG(wait_time_minutes), 2) AS avg_wait_time,
    ROUND(AVG(surge_multiplier), 2) AS avg_surge
FROM rides
GROUP BY city, is_high_demand;


-- ============================================================
-- CITY DETERIORATION VIEW
-- ============================================================

-- Grain: One row per city
-- Purpose: Quantify deterioration during high demand
CREATE VIEW IF NOT EXISTS vw_city_deterioration AS
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
JOIN city_high h ON n.city = h.city;


-- ============================================================
-- RIDER EXPERIENCE VIEW
-- ============================================================

-- Grain: One row per city
-- Purpose: Focus on rider-facing experience metrics
CREATE VIEW IF NOT EXISTS vw_rider_experience AS
SELECT
    city,
    COUNT(*) AS total_rides,
    ROUND(AVG(wait_time_minutes), 2) AS avg_wait_time,
    ROUND(SUM(rider_cancelled) * 100.0 / COUNT(*), 2) AS rider_cancel_rate,
    ROUND(SUM(ride_completed) * 100.0 / COUNT(*), 2) AS completion_rate,
    ROUND(AVG(surge_multiplier), 2) AS avg_surge,
    ROUND(SUM(CASE WHEN wait_time_minutes > 10 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS pct_long_wait,
    ROUND(SUM(CASE WHEN surge_multiplier > 1.5 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS pct_high_surge
FROM rides
GROUP BY city;


-- ============================================================
-- DAILY AGGREGATION TABLE
-- ============================================================

-- Grain: One row per day
-- Purpose: Pre-aggregated daily metrics for trend analysis
CREATE TABLE IF NOT EXISTS agg_daily_metrics (
    ride_date TEXT PRIMARY KEY,
    ride_count INTEGER,
    acceptance_rate REAL,
    completion_rate REAL,
    rider_cancel_rate REAL,
    avg_wait_time REAL,
    avg_surge REAL,
    high_demand_share REAL,
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Populate aggregation table
INSERT OR REPLACE INTO agg_daily_metrics (ride_date, ride_count, acceptance_rate, completion_rate, rider_cancel_rate, avg_wait_time, avg_surge, high_demand_share)
SELECT
    DATE(request_timestamp) AS ride_date,
    COUNT(*) AS ride_count,
    ROUND(SUM(was_accepted) * 100.0 / COUNT(*), 2) AS acceptance_rate,
    ROUND(SUM(ride_completed) * 100.0 / COUNT(*), 2) AS completion_rate,
    ROUND(SUM(rider_cancelled) * 100.0 / COUNT(*), 2) AS rider_cancel_rate,
    ROUND(AVG(wait_time_minutes), 2) AS avg_wait_time,
    ROUND(AVG(surge_multiplier), 2) AS avg_surge,
    ROUND(SUM(CASE WHEN is_high_demand = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS high_demand_share
FROM rides
GROUP BY DATE(request_timestamp);


-- ============================================================
-- CITY AGGREGATION TABLE
-- ============================================================

-- Grain: One row per city
-- Purpose: Pre-aggregated city metrics for fast city-level queries
CREATE TABLE IF NOT EXISTS agg_city_metrics (
    city TEXT PRIMARY KEY,
    ride_volume INTEGER,
    acceptance_rate REAL,
    completion_rate REAL,
    rider_cancel_rate REAL,
    driver_cancel_rate REAL,
    avg_wait_time REAL,
    avg_surge REAL,
    high_demand_share REAL,
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Populate aggregation table
INSERT OR REPLACE INTO agg_city_metrics (city, ride_volume, acceptance_rate, completion_rate, rider_cancel_rate, driver_cancel_rate, avg_wait_time, avg_surge, high_demand_share)
SELECT
    city,
    COUNT(*) AS ride_volume,
    ROUND(SUM(was_accepted) * 100.0 / COUNT(*), 2) AS acceptance_rate,
    ROUND(SUM(ride_completed) * 100.0 / COUNT(*), 2) AS completion_rate,
    ROUND(SUM(rider_cancelled) * 100.0 / COUNT(*), 2) AS rider_cancel_rate,
    ROUND(SUM(driver_cancelled) * 100.0 / COUNT(*), 2) AS driver_cancel_rate,
    ROUND(AVG(wait_time_minutes), 2) AS avg_wait_time,
    ROUND(AVG(surge_multiplier), 2) AS avg_surge,
    ROUND(SUM(CASE WHEN is_high_demand = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS high_demand_share
FROM rides
GROUP BY city;
