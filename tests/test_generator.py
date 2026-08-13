"""Tests for the synthetic ride dataset generator."""

from __future__ import annotations

import pytest
import pandas as pd

from roadies.ingestion.generator import (
    CANCELLATION_REASONS,
    CITIES,
    DEMAND_LEVELS,
    RAW_COLUMNS,
    generate_rides,
)


@pytest.fixture
def small_df():
    """Generate a small dataset for testing."""
    return generate_rides(n_rows=500, seed=42)


@pytest.fixture
def medium_df():
    """Generate a medium dataset for broader testing."""
    return generate_rides(n_rows=5_000, seed=99)


class TestRowCount:
    def test_requested_row_count(self, small_df):
        assert len(small_df) == 500

    def test_medium_row_count(self, medium_df):
        assert len(medium_df) == 5_000


class TestRequiredColumns:
    def test_all_columns_present(self, small_df):
        missing = set(RAW_COLUMNS) - set(small_df.columns)
        assert not missing, f"Missing columns: {missing}"

    def test_no_extra_columns(self, small_df):
        extra = set(small_df.columns) - set(RAW_COLUMNS)
        assert not extra, f"Unexpected columns: {extra}"


class TestUniqueRideIds:
    def test_ride_ids_unique(self, small_df):
        assert small_df["ride_id"].is_unique

    def test_ride_ids_format(self, small_df):
        assert small_df["ride_id"].str.match(r"^R-\d{6}$").all()


class TestReproducibility:
    def test_same_seed_same_output(self):
        df1 = generate_rides(n_rows=200, seed=123)
        df2 = generate_rides(n_rows=200, seed=123)
        assert df1.equals(df2)

    def test_different_seed_different_output(self):
        df1 = generate_rides(n_rows=200, seed=123)
        df2 = generate_rides(n_rows=200, seed=456)
        assert not df1.equals(df2)


class TestCategoricalValues:
    def test_valid_cities(self, small_df):
        assert set(small_df["city"].unique()) <= set(CITIES)

    def test_multiple_cities(self, small_df):
        assert small_df["city"].nunique() >= 3

    def test_valid_demand_levels(self, small_df):
        assert set(small_df["demand_level"].unique()) <= set(DEMAND_LEVELS)


class TestNumericRanges:
    def test_surge_multiplier_range(self, small_df):
        assert small_df["surge_multiplier"].between(1.0, 5.0).all()

    def test_base_fare_range(self, small_df):
        assert small_df["base_fare"].between(50.0, 500.0).all()

    def test_wait_time_range_or_null(self, small_df):
        wait = small_df["wait_time_minutes"].dropna()
        assert wait.between(0.0, 60.0).all()

    def test_trip_duration_range_or_null(self, small_df):
        dur = small_df["trip_duration_minutes"].dropna()
        assert dur.between(0.0, 120.0).all()

    def test_trip_distance_range_or_null(self, small_df):
        dist = small_df["trip_distance_km"].dropna()
        assert dist.between(0.0, 50.0).all()

    def test_driver_acceptance_rate_range_or_null(self, small_df):
        rate = small_df["driver_acceptance_rate"].dropna()
        assert rate.between(0.0, 1.0).all()

    def test_driver_rating_range_or_null(self, small_df):
        rating = small_df["driver_rating"].dropna()
        assert rating.between(1.0, 5.0).all()


class TestCancellationConsistency:
    def test_completed_implies_accepted(self, small_df):
        completed_not_accepted = small_df[small_df["completed"] & ~small_df["accepted"]]
        assert len(completed_not_accepted) == 0

    def test_cancelled_by_driver_implies_accepted(self, small_df):
        cd_not_accepted = small_df[
            small_df["cancelled_by_driver"] & ~small_df["accepted"]
        ]
        assert len(cd_not_accepted) == 0

    def test_cancelled_by_rider_implies_not_completed(self, small_df):
        cr_and_completed = small_df[
            small_df["cancelled_by_rider"] & small_df["completed"]
        ]
        assert len(cr_and_completed) == 0

    def test_cancellation_reason_null_when_not_cancelled(self, small_df):
        not_cancelled = small_df[
            ~small_df["cancelled_by_rider"] & ~small_df["cancelled_by_driver"]
        ]
        assert not_cancelled["cancellation_reason"].isnull().all()

    def test_cancellation_reason_present_when_cancelled(self, small_df):
        cancelled = small_df[
            small_df["cancelled_by_rider"] | small_df["cancelled_by_driver"]
        ]
        assert cancelled["cancellation_reason"].notnull().all()

    def test_valid_cancellation_reasons(self, small_df):
        reasons = small_df["cancellation_reason"].dropna().unique()
        assert set(reasons) <= set(CANCELLATION_REASONS)


class TestTimeRepresentation:
    def test_multiple_days(self, small_df):
        dates = small_df["request_timestamp"].dt.date.nunique()
        assert dates >= 3

    def test_multiple_hours(self, small_df):
        hours = small_df["request_timestamp"].dt.hour.nunique()
        assert hours >= 10

    def test_timestamps_are_datetime(self, small_df):
        assert pd.api.types.is_datetime64_any_dtype(small_df["request_timestamp"])


class TestCityHourConsistency:
    def test_city_hour_groups_share_context(self, small_df):
        # Group by city + hour and verify denormalised values are consistent
        grouped = small_df.groupby(["city", "request_timestamp"])
        for name, group in grouped:
            assert group["city_hour_requested_rides"].nunique() == 1
            assert group["city_hour_available_drivers"].nunique() == 1
            assert group["demand_level"].nunique() == 1
