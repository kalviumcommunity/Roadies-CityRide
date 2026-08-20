-- Roadies-CityRide Advanced SQL Analysis
-- Joins, window functions, and advanced analytical queries

-- ============================================================
-- CITY RANKINGS
-- ============================================================

-- Rank cities by high-demand rider cancellation rate
-- Uses window function RANK() over cancellation rate
SELECT
    city,
    SUM(rider_cancelled) AS rider_cancellations,
    COUNT(*) AS total_rides,
    ROUND(SUM(rider_cancelled) * 100.0 / COUNT(*), 2) AS cancel_rate,
    RANK() OVER (ORDER BY SUM(rider_cancelled) * 100.0 / COUNT(*) DESC) AS cancel_rank
FROM rides
WHERE is_high_demand = 1
GROUP BY city
ORDER BY cancel_rank;


-- Rank cities by acceptance deterioration during high demand
-- Compares high-demand acceptance vs overall
WITH city_stats AS (
    SELECT
        city,
        ROUND(SUM(CASE WHEN is_high_demand = 1 THEN was_accepted ELSE 0 END) * 100.0 /
              NULLIF(SUM(CASE WHEN is_high_demand = 1 THEN 1 ELSE 0 END), 0), 2) AS high_acceptance,
        ROUND(SUM(CASE WHEN is_high_demand = 0 THEN was_accepted ELSE 0 END) * 100.0 /
              NULLIF(SUM(CASE WHEN is_high_demand = 0 THEN 1 ELSE 0 END), 0), 2) AS normal_acceptance
    FROM rides
    GROUP BY city
)
SELECT
    city,
    normal_acceptance,
    high_acceptance,
    ROUND(normal_acceptance - high_acceptance, 2) AS deterioration,
    RANK() OVER (ORDER BY normal_acceptance - high_acceptance DESC) AS deterioration_rank
FROM city_stats
ORDER BY deterioration_rank;


-- ============================================================
-- WITHIN-CITY BASELINE COMPARISON
-- ============================================================

-- Compare each city's high-demand metrics against its own normal baseline
WITH city_normal AS (
    SELECT
        city,
        ROUND(AVG(wait_time_minutes), 2) AS normal_wait,
        ROUND(AVG(surge_multiplier), 2) AS normal_surge,
        ROUND(SUM(rider_cancelled) * 100.0 / COUNT(*), 2) AS normal_cancel
    FROM rides
    WHERE is_high_demand = 0
    GROUP BY city
),
city_high AS (
    SELECT
        city,
        ROUND(AVG(wait_time_minutes), 2) AS high_wait,
        ROUND(AVG(surge_multiplier), 2) AS high_surge,
        ROUND(SUM(rider_cancelled) * 100.0 / COUNT(*), 2) AS high_cancel
    FROM rides
    WHERE is_high_demand = 1
    GROUP BY city
)
SELECT
    n.city,
    n.normal_wait,
    h.high_wait,
    ROUND(h.high_wait - n.normal_wait, 2) AS wait_change,
    ROUND((h.high_wait - n.normal_wait) / n.normal_wait * 100, 2) AS wait_change_pct,
    n.normal_surge,
    h.high_surge,
    ROUND(h.high_surge - n.normal_surge, 2) AS surge_change,
    n.normal_cancel,
    h.high_cancel,
    ROUND(h.high_cancel - n.normal_cancel, 2) AS cancel_change
FROM city_normal n
JOIN city_high h ON n.city = h.city
ORDER BY cancel_change DESC;


-- ============================================================
-- RUNNING/ROLLING METRICS
-- ============================================================

-- Daily ride volume with running total and 7-day moving average
SELECT
    DATE(request_timestamp) AS ride_date,
    COUNT(*) AS daily_rides,
    SUM(COUNT(*)) OVER (ORDER BY DATE(request_timestamp)) AS running_total,
    ROUND(AVG(COUNT(*)) OVER (
        ORDER BY DATE(request_timestamp)
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ), 0) AS moving_avg_7day
FROM rides
GROUP BY DATE(request_timestamp)
ORDER BY ride_date;


-- ============================================================
-- CITY CONTRIBUTION ANALYSIS
-- ============================================================

-- Each city's contribution to total rides and cancellations
WITH city_contributions AS (
    SELECT
        city,
        COUNT(*) AS city_rides,
        SUM(rider_cancelled) AS city_cancellations,
        SUM(driver_cancelled) AS driver_cancellations
    FROM rides
    GROUP BY city
),
totals AS (
    SELECT
        SUM(city_rides) AS total_rides,
        SUM(city_cancellations) AS total_cancellations,
        SUM(driver_cancellations) AS total_driver_cancellations
    FROM city_contributions
)
SELECT
    c.city,
    c.city_rides,
    ROUND(c.city_rides * 100.0 / t.total_rides, 2) AS ride_share_pct,
    c.city_cancellations,
    ROUND(c.city_cancellations * 100.0 / t.total_cancellations, 2) AS cancel_share_pct,
    c.driver_cancellations,
    ROUND(c.driver_cancellations * 100.0 / t.total_driver_cancellations, 2) AS driver_cancel_share_pct
FROM city_contributions c
CROSS JOIN totals t
ORDER BY cancel_share_pct DESC;


-- ============================================================
-- CITY DEVIATION FROM AVERAGE
-- ============================================================

-- How each city compares to the overall average
WITH city_metrics AS (
    SELECT
        city,
        ROUND(AVG(wait_time_minutes), 2) AS avg_wait,
        ROUND(AVG(surge_multiplier), 2) AS avg_surge,
        ROUND(SUM(rider_cancelled) * 100.0 / COUNT(*), 2) AS cancel_rate
    FROM rides
    GROUP BY city
),
global_avg AS (
    SELECT
        ROUND(AVG(avg_wait), 2) AS global_avg_wait,
        ROUND(AVG(avg_surge), 2) AS global_avg_surge,
        ROUND(AVG(cancel_rate), 2) AS global_cancel_rate
    FROM city_metrics
)
SELECT
    c.city,
    c.avg_wait,
    g.global_avg_wait,
    ROUND(c.avg_wait - g.global_avg_wait, 2) AS wait_vs_avg,
    c.avg_surge,
    g.global_avg_surge,
    ROUND(c.avg_surge - g.global_avg_surge, 2) AS surge_vs_avg,
    c.cancel_rate,
    g.global_cancel_rate,
    ROUND(c.cancel_rate - g.global_cancel_rate, 2) AS cancel_vs_avg
FROM city_metrics c
CROSS JOIN global_avg g
ORDER BY cancel_vs_avg DESC;


-- ============================================================
-- HIGH-DEMAND CITY PAIRING
-- ============================================================

-- Compare each city's normal vs high demand with percentile ranking
WITH city_demand_stats AS (
    SELECT
        city,
        is_high_demand,
        ROUND(SUM(rider_cancelled) * 100.0 / COUNT(*), 2) AS cancel_rate,
        ROUND(AVG(wait_time_minutes), 2) AS avg_wait
    FROM rides
    GROUP BY city, is_high_demand
)
SELECT
    n.city,
    n.cancel_rate AS normal_cancel,
    h.cancel_rate AS high_cancel,
    ROUND(h.cancel_rate - n.cancel_rate, 2) AS cancel_deterioration,
    PERCENT_RANK() OVER (ORDER BY h.cancel_rate - n.cancel_rate DESC) AS deterioration_percentile
FROM city_demand_stats n
JOIN city_demand_stats h
    ON n.city = h.city
    AND n.is_high_demand = 0
    AND h.is_high_demand = 1
ORDER BY deterioration_percentile;
