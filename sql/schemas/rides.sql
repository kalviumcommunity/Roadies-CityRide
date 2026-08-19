-- Roadies-CityRide Analytical Database Schema
-- SQLite schema for ride-level analytical data

CREATE TABLE IF NOT EXISTS rides (
    ride_id TEXT PRIMARY KEY,
    rider_id TEXT,
    driver_id TEXT,
    city TEXT NOT NULL,
    vehicle_type TEXT,
    ride_distance_km REAL,
    ride_duration_minutes REAL,
    base_fare REAL,
    total_fare REAL,
    payment_method TEXT,
    rider_rating REAL,
    driver_rating REAL,
    request_timestamp TEXT,
    pickup_latitude REAL,
    pickup_longitude REAL,
    dropoff_latitude REAL,
    dropoff_longitude REAL,
    was_accepted INTEGER,
    ride_completed INTEGER,
    rider_cancelled INTEGER,
    driver_cancelled INTEGER,
    wait_time_minutes REAL,
    surge_multiplier REAL,
    demand_supply_ratio REAL,
    available_drivers INTEGER,
    requested_rides INTEGER,
    is_high_demand INTEGER,
    demand_period TEXT,
    surge_category TEXT,
    acceptance_rate_band TEXT,
    time_period TEXT,
    is_weekend INTEGER,
    hour_of_day INTEGER,
    day_of_week INTEGER,
    experience_status TEXT,
    cancellation_reason TEXT,
    cancellation_reason_category TEXT
);

CREATE INDEX IF NOT EXISTS idx_rides_city ON rides(city);
CREATE INDEX IF NOT EXISTS idx_rides_timestamp ON rides(request_timestamp);
CREATE INDEX IF NOT EXISTS idx_rides_demand ON rides(is_high_demand);
CREATE INDEX IF NOT EXISTS idx_rides_rider ON rides(rider_id);
CREATE INDEX IF NOT EXISTS idx_rides_driver ON rides(driver_id);
