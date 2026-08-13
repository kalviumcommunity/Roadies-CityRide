"""Synthetic ride-sharing dataset generator.

Generates a reproducible dataset following the schema in docs/data_dictionary.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CITIES: list[str] = ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Pune"]

CANCELLATION_REASONS: list[str] = [
    "Long wait time",
    "Driver rude",
    "Changed mind",
    "Vehicle quality",
    "Other",
]

DEMAND_LEVELS: list[str] = ["low", "medium", "high", "critical"]

RAW_COLUMNS: list[str] = [
    "ride_id",
    "rider_id",
    "driver_id",
    "request_timestamp",
    "city",
    "accepted",
    "completed",
    "cancelled_by_rider",
    "cancelled_by_driver",
    "cancellation_reason",
    "driver_acceptance_rate",
    "driver_rating",
    "city_hour_requested_rides",
    "city_hour_available_drivers",
    "demand_level",
    "surge_multiplier",
    "base_fare",
    "wait_time_minutes",
    "trip_duration_minutes",
    "trip_distance_km",
]

# ---------------------------------------------------------------------------
# City profiles – each city has different baseline characteristics
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CityProfile:
    """Baseline characteristics for a city."""

    name: str
    base_demand: float  # average rides per hour at baseline
    driver_density: float  # available drivers per ride at baseline
    base_acceptance_rate: float  # baseline driver acceptance probability
    base_driver_rating: float  # mean driver rating
    base_surge: float  # mean surge multiplier at baseline
    base_wait: float  # mean wait time in minutes at baseline
    base_fare: float  # mean base fare in INR
    cancellation_bias: float  # additional cancellation probability


_CITY_PROFILES: dict[str, CityProfile] = {
    "Mumbai": CityProfile(
        name="Mumbai",
        base_demand=85,
        driver_density=0.45,
        base_acceptance_rate=0.78,
        base_driver_rating=4.2,
        base_surge=1.3,
        base_wait=8.0,
        base_fare=130.0,
        cancellation_bias=0.03,
    ),
    "Delhi": CityProfile(
        name="Delhi",
        base_demand=80,
        driver_density=0.50,
        base_acceptance_rate=0.80,
        base_driver_rating=4.1,
        base_surge=1.2,
        base_wait=7.5,
        base_fare=110.0,
        cancellation_bias=0.02,
    ),
    "Bangalore": CityProfile(
        name="Bangalore",
        base_demand=75,
        driver_density=0.55,
        base_acceptance_rate=0.85,
        base_driver_rating=4.4,
        base_surge=1.15,
        base_wait=6.5,
        base_fare=100.0,
        cancellation_bias=0.01,
    ),
    "Hyderabad": CityProfile(
        name="Hyderabad",
        base_demand=60,
        driver_density=0.50,
        base_acceptance_rate=0.82,
        base_driver_rating=4.3,
        base_surge=1.1,
        base_wait=7.0,
        base_fare=90.0,
        cancellation_bias=0.02,
    ),
    "Chennai": CityProfile(
        name="Chennai",
        base_demand=55,
        driver_density=0.48,
        base_acceptance_rate=0.80,
        base_driver_rating=4.2,
        base_surge=1.15,
        base_wait=7.5,
        base_fare=95.0,
        cancellation_bias=0.02,
    ),
    "Pune": CityProfile(
        name="Pune",
        base_demand=45,
        driver_density=0.42,
        base_acceptance_rate=0.76,
        base_driver_rating=4.1,
        base_surge=1.25,
        base_wait=9.0,
        base_fare=85.0,
        cancellation_bias=0.04,
    ),
}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _demand_multiplier(hour: int, is_weekend: bool) -> float:
    """Return a demand multiplier based on hour of day and weekend status."""
    # Peak hours: 7-9, 17-20
    if hour in (7, 8, 17, 18, 19, 20):
        base = 1.8
    elif hour in (9, 10, 16, 21):
        base = 1.3
    elif hour in (11, 12, 13, 14, 15):
        base = 1.0
    elif hour in (22, 23, 0, 1):
        base = 0.6
    else:  # 2-6
        base = 0.3

    if is_weekend:
        base *= 1.2  # slightly higher demand on weekends

    return base


def _demand_level_from_count(count: int) -> str:
    """Classify demand level from ride count."""
    if count < 30:
        return "low"
    elif count < 70:
        return "medium"
    elif count < 120:
        return "high"
    else:
        return "critical"


def _validate_dataframe(df: pd.DataFrame) -> None:
    """Validate the generated DataFrame against the schema."""
    # Check columns
    missing = set(RAW_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    # Check row count
    if len(df) == 0:
        raise ValueError("Generated DataFrame is empty")

    # Check unique ride IDs
    if df["ride_id"].duplicated().any():
        raise ValueError("Duplicate ride_id values found")

    # Check required fields are not null
    required_non_null = [
        "ride_id",
        "rider_id",
        "request_timestamp",
        "city",
        "accepted",
        "completed",
        "cancelled_by_rider",
        "cancelled_by_driver",
        "city_hour_requested_rides",
        "city_hour_available_drivers",
        "demand_level",
        "surge_multiplier",
        "base_fare",
    ]
    for col in required_non_null:
        if df[col].isnull().any():
            raise ValueError(f"Required field '{col}' contains null values")

    # Check categorical values
    if not df["city"].isin(CITIES).all():
        invalid = df[~df["city"].isin(CITIES)]["city"].unique()
        raise ValueError(f"Invalid city values: {invalid}")

    if not df["demand_level"].isin(DEMAND_LEVELS).all():
        invalid = df[~df["demand_level"].isin(DEMAND_LEVELS)]["demand_level"].unique()
        raise ValueError(f"Invalid demand_level values: {invalid}")

    # Check numeric ranges
    if (df["surge_multiplier"] < 1.0).any() or (df["surge_multiplier"] > 5.0).any():
        raise ValueError("surge_multiplier out of range [1.0, 5.0]")

    if (df["base_fare"] < 50.0).any() or (df["base_fare"] > 500.0).any():
        raise ValueError("base_fare out of range [50.0, 500.0]")

    # Check logical consistency
    completed_without_accepted = df[df["completed"] & ~df["accepted"]]
    if len(completed_without_accepted) > 0:
        raise ValueError("completed=True where accepted=False")

    cancelled_by_driver_without_accepted = df[
        df["cancelled_by_driver"] & ~df["accepted"]
    ]
    if len(cancelled_by_driver_without_accepted) > 0:
        raise ValueError("cancelled_by_driver=True where accepted=False")

    cancelled_rider_and_completed = df[df["cancelled_by_rider"] & df["completed"]]
    if len(cancelled_rider_and_completed) > 0:
        raise ValueError("cancelled_by_rider=True where completed=True")


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------


def generate_rides(
    n_rows: int = 50_000,
    seed: int = 42,
    start_date: str = "2025-07-01",
    end_date: str = "2025-09-28",
) -> pd.DataFrame:
    """Generate a synthetic ride-sharing dataset.

    Parameters
    ----------
    n_rows:
        Number of ride requests to generate.
    seed:
        Random seed for reproducibility.
    start_date:
        Start date for the time range (ISO format).
    end_date:
        End date for the time range (ISO format).

    Returns
    -------
    pd.DataFrame
        DataFrame with 20 raw fields following the schema.
    """
    rng = np.random.default_rng(seed)

    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)
    date_range = pd.date_range(start, end, freq="h")

    # Generate city-hour combinations
    city_hour_records: list[dict] = []
    for ts in date_range:
        hour = ts.hour
        is_weekend = ts.dayofweek >= 5  # Saturday=5, Sunday=6
        for city, profile in _CITY_PROFILES.items():
            mult = _demand_multiplier(hour, is_weekend)
            n_requested = max(
                1, int(rng.poisson(profile.base_demand * mult))
            )
            n_available = max(
                0, int(rng.poisson(n_requested * profile.driver_density))
            )
            demand_level = _demand_level_from_count(n_requested)

            city_hour_records.append(
                {
                    "timestamp": ts,
                    "city": city,
                    "hour": hour,
                    "is_weekend": is_weekend,
                    "n_requested": n_requested,
                    "n_available": n_available,
                    "demand_level": demand_level,
                    "profile": profile,
                }
            )

    # Distribute rides across city-hours proportionally
    total_requested = sum(r["n_requested"] for r in city_hour_records)
    rides_per_ch = [
        max(1, int(round(n_rows * r["n_requested"] / total_requested)))
        for r in city_hour_records
    ]

    # Adjust to match exact n_rows
    diff = n_rows - sum(rides_per_ch)
    for i in range(abs(diff)):
        idx = i % len(rides_per_ch)
        rides_per_ch[idx] += 1 if diff > 0 else -1

    # Build ride records
    ride_records: list[dict] = []
    ride_counter = 0
    rider_counter = 0

    for ch_idx, ch in enumerate(city_hour_records):
        n_rides = rides_per_ch[ch_idx]
        if n_rides <= 0:
            continue

        profile: CityProfile = ch["profile"]
        ts: pd.Timestamp = ch["timestamp"]
        n_available: int = ch["n_available"]
        n_requested_city: int = ch["n_requested"]
        demand_level: str = ch["demand_level"]

        # Surge increases with demand pressure
        supply_pressure = n_requested_city / max(1, n_available)
        surge_base = profile.base_surge + 0.3 * max(0, supply_pressure - 1.5)
        surge_base = min(5.0, max(1.0, surge_base))

        # Driver acceptance rate decreases with pressure
        acceptance_pressure = max(0, supply_pressure - 1.2) * 0.1

        for _ in range(n_rides):
            ride_counter += 1
            rider_counter += 1

            ride_id = f"R-{ride_counter:06d}"
            rider_id = f"RDR-{rider_counter:06d}"

            # Stagger timestamps within the hour
            minute_offset = rng.integers(0, 60)
            second_offset = rng.integers(0, 60)
            ride_ts = ts + pd.Timedelta(minutes=int(minute_offset), seconds=int(second_offset))

            # Driver assignment and acceptance
            driver_assigned = rng.random() < min(1.0, n_available / max(1, n_requested_city))

            if driver_assigned:
                driver_id = f"DRV-{rng.integers(1, 500):06d}"
                # Acceptance probability decreases with pressure
                accept_prob = max(
                    0.3,
                    profile.base_acceptance_rate - acceptance_pressure + rng.normal(0, 0.05),
                )
                accepted = rng.random() < accept_prob

                if accepted:
                    # Driver rating with noise
                    driver_rating = float(
                        np.clip(
                            rng.normal(profile.base_driver_rating, 0.3),
                            1.0,
                            5.0,
                        )
                    )
                    # Acceptance rate with noise
                    driver_acceptance_rate = float(
                        np.clip(
                            rng.normal(profile.base_acceptance_rate, 0.1),
                            0.0,
                            1.0,
                        )
                    )

                    # Wait time increases with supply pressure
                    wait_base = profile.base_wait * (1 + 0.2 * max(0, supply_pressure - 1.0))
                    wait_time = float(
                        np.clip(rng.exponential(wait_base), 0.5, 60.0)
                    )

                    # Determine ride outcome
                    cancel_prob_rider = profile.cancellation_bias + 0.03 * max(
                        0, supply_pressure - 1.5
                    ) + 0.01 * max(0, wait_time - 10)
                    cancel_prob_driver = 0.02 + 0.01 * max(0, supply_pressure - 2.0)

                    cancelled_by_rider = rng.random() < min(0.4, cancel_prob_rider)
                    cancelled_by_driver = (
                        not cancelled_by_rider
                        and rng.random() < min(0.2, cancel_prob_driver)
                    )

                    completed = not cancelled_by_rider and not cancelled_by_driver

                    # Cancellation reason
                    cancellation_reason = None
                    if cancelled_by_rider:
                        # Weight "Long wait time" more when wait is high
                        if wait_time > 10:
                            weights = [0.4, 0.15, 0.2, 0.15, 0.1]
                        else:
                            weights = [0.15, 0.15, 0.35, 0.15, 0.2]
                        cancellation_reason = rng.choice(
                            CANCELLATION_REASONS, p=weights
                        )
                    elif cancelled_by_driver:
                        cancellation_reason = rng.choice(
                            ["Vehicle quality", "Other"], p=[0.4, 0.6]
                        )

                    # Trip characteristics (only if completed)
                    if completed:
                        trip_distance = float(
                            np.clip(rng.exponential(8.0), 0.5, 50.0)
                        )
                        trip_duration = float(
                            np.clip(trip_distance * rng.normal(2.5, 0.5), 1.0, 120.0)
                        )
                    else:
                        trip_distance = None
                        trip_duration = None

                else:
                    # Driver rejected
                    driver_rating = None
                    driver_acceptance_rate = None
                    wait_time = None
                    cancelled_by_rider = False
                    cancelled_by_driver = False
                    cancellation_reason = None
                    completed = False
                    trip_distance = None
                    trip_duration = None

            else:
                # No driver assigned
                driver_id = None
                driver_rating = None
                driver_acceptance_rate = None
                wait_time = None
                cancelled_by_rider = False
                cancelled_by_driver = False
                cancellation_reason = None
                completed = False
                trip_distance = None
                trip_duration = None

            # Surge multiplier with noise
            surge = float(np.clip(rng.normal(surge_base, 0.15), 1.0, 5.0))

            # Base fare with noise
            base_fare = float(np.clip(rng.normal(profile.base_fare, 10.0), 50.0, 500.0))

            ride_records.append(
                {
                    "ride_id": ride_id,
                    "rider_id": rider_id,
                    "driver_id": driver_id,
                    "request_timestamp": ride_ts,
                    "city": profile.name,
                    "accepted": bool(accepted) if driver_assigned else False,
                    "completed": bool(completed),
                    "cancelled_by_rider": bool(cancelled_by_rider),
                    "cancelled_by_driver": bool(cancelled_by_driver),
                    "cancellation_reason": cancellation_reason,
                    "driver_acceptance_rate": driver_acceptance_rate,
                    "driver_rating": driver_rating,
                    "city_hour_requested_rides": n_requested_city,
                    "city_hour_available_drivers": n_available,
                    "demand_level": demand_level,
                    "surge_multiplier": surge,
                    "base_fare": base_fare,
                    "wait_time_minutes": wait_time,
                    "trip_duration_minutes": trip_duration,
                    "trip_distance_km": trip_distance,
                }
            )

    df = pd.DataFrame(ride_records, columns=RAW_COLUMNS)

    # Validate
    _validate_dataframe(df)

    return df
