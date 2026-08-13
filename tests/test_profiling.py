"""Tests for dataset profiling."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from roadies.quality.profiler import (
    ColumnProfile,
    DatasetProfile,
    profile_dataset,
    save_profile_report,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_sample_df() -> pd.DataFrame:
    """Create a small sample DataFrame for testing."""
    return pd.DataFrame({
        "ride_id": [f"R-{i:06d}" for i in range(1, 11)],
        "rider_id": [f"RDR-{i:04d}" for i in range(1, 11)],
        "driver_id": [f"DRV-{i:04d}" if i % 3 != 0 else None for i in range(1, 11)],
        "request_timestamp": pd.date_range("2025-08-01T08:00:00", periods=10, freq="h"),
        "city": ["Mumbai", "Delhi", "Bangalore", "Mumbai", "Delhi",
                 "Chennai", "Pune", "Hyderabad", "Mumbai", "Delhi"],
        "accepted": [True, True, False, True, True, False, True, True, True, False],
        "completed": [True, True, False, True, False, False, True, True, True, False],
        "cancelled_by_rider": [False, False, False, False, True, False, False, False, False, True],
        "cancelled_by_driver": [False, False, False, False, False, False, False, False, False, False],
        "cancellation_reason": [None, None, None, None, "Changed mind", None, None, None, None, "Long wait time"],
        "driver_acceptance_rate": [0.85, 0.90, None, 0.78, 0.82, None, 0.88, 0.91, 0.80, None],
        "driver_rating": [4.5, 4.2, None, 4.0, 4.3, None, 4.6, 4.8, 4.1, None],
        "city_hour_requested_rides": [100, 80, 120, 95, 85, 70, 60, 55, 110, 90],
        "city_hour_available_drivers": [30, 25, 40, 28, 20, 18, 15, 12, 35, 22],
        "demand_level": ["high", "medium", "high", "medium", "high", "medium", "low", "low", "high", "medium"],
        "surge_multiplier": [1.5, 1.2, 1.8, 1.3, 1.6, 1.1, 1.0, 1.0, 1.7, 1.4],
        "base_fare": [120.0, 100.0, 130.0, 110.0, 125.0, 95.0, 85.0, 80.0, 135.0, 105.0],
        "wait_time_minutes": [5.0, 3.0, None, 7.0, 4.0, None, 2.0, 1.5, 6.0, None],
        "trip_duration_minutes": [20.0, 15.0, None, 25.0, None, None, 18.0, 12.0, 22.0, None],
        "trip_distance_km": [8.0, 5.0, None, 10.0, None, None, 7.0, 4.0, 9.0, None],
    })


# ---------------------------------------------------------------------------
# Profile result structure
# ---------------------------------------------------------------------------

class TestProfileStructure:
    def test_returns_dataset_profile(self) -> None:
        df = _make_sample_df()
        result = profile_dataset(df)
        assert isinstance(result, DatasetProfile)

    def test_has_column_profiles(self) -> None:
        df = _make_sample_df()
        result = profile_dataset(df)
        assert len(result.columns) == len(df.columns)

    def test_column_profiles_are_column_profile_instances(self) -> None:
        df = _make_sample_df()
        result = profile_dataset(df)
        for col in result.columns:
            assert isinstance(col, ColumnProfile)


# ---------------------------------------------------------------------------
# Row/column counts
# ---------------------------------------------------------------------------

class TestRowColumnCounts:
    def test_total_rows(self) -> None:
        df = _make_sample_df()
        result = profile_dataset(df)
        assert result.total_rows == 10

    def test_total_columns(self) -> None:
        df = _make_sample_df()
        result = profile_dataset(df)
        assert result.total_columns == 20

    def test_column_profile_row_count(self) -> None:
        df = _make_sample_df()
        result = profile_dataset(df)
        for col in result.columns:
            assert col.row_count == 10


# ---------------------------------------------------------------------------
# Null counts
# ---------------------------------------------------------------------------

class TestNullCounts:
    def test_driver_id_has_nulls(self) -> None:
        df = _make_sample_df()
        result = profile_dataset(df)
        driver_col = next(c for c in result.columns if c.name == "driver_id")
        assert driver_col.null_count > 0

    def test_ride_id_has_no_nulls(self) -> None:
        df = _make_sample_df()
        result = profile_dataset(df)
        ride_col = next(c for c in result.columns if c.name == "ride_id")
        assert ride_col.null_count == 0

    def test_null_percentage_calculation(self) -> None:
        df = _make_sample_df()
        result = profile_dataset(df)
        driver_col = next(c for c in result.columns if c.name == "driver_id")
        expected_pct = driver_col.null_count / driver_col.row_count * 100
        assert abs(driver_col.null_pct - round(expected_pct, 2)) < 0.01


# ---------------------------------------------------------------------------
# Unique counts
# ---------------------------------------------------------------------------

class TestUniqueCounts:
    def test_ride_ids_all_unique(self) -> None:
        df = _make_sample_df()
        result = profile_dataset(df)
        ride_col = next(c for c in result.columns if c.name == "ride_id")
        assert ride_col.unique_count == 10

    def test_city_unique_count(self) -> None:
        df = _make_sample_df()
        result = profile_dataset(df)
        city_col = next(c for c in result.columns if c.name == "city")
        assert city_col.unique_count == 6


# ---------------------------------------------------------------------------
# Numeric statistics
# ---------------------------------------------------------------------------

class TestNumericStatistics:
    def test_surge_multiplier_stats(self) -> None:
        df = _make_sample_df()
        result = profile_dataset(df)
        surge_col = next(c for c in result.columns if c.name == "surge_multiplier")
        assert surge_col.min is not None
        assert surge_col.max is not None
        assert surge_col.mean is not None
        assert surge_col.median is not None
        assert surge_col.std is not None
        assert surge_col.min == 1.0
        assert surge_col.max == 1.8

    def test_wait_time_stats(self) -> None:
        df = _make_sample_df()
        result = profile_dataset(df)
        wait_col = next(c for c in result.columns if c.name == "wait_time_minutes")
        assert wait_col.min is not None
        assert wait_col.p25 is not None
        assert wait_col.p75 is not None
        assert wait_col.p95 is not None


# ---------------------------------------------------------------------------
# Categorical statistics
# ---------------------------------------------------------------------------

class TestCategoricalStatistics:
    def test_city_top_values(self) -> None:
        df = _make_sample_df()
        result = profile_dataset(df)
        city_col = next(c for c in result.columns if c.name == "city")
        assert len(city_col.top_values) > 0
        assert "Mumbai" in city_col.top_values

    def test_demand_level_top_values(self) -> None:
        df = _make_sample_df()
        result = profile_dataset(df)
        demand_col = next(c for c in result.columns if c.name == "demand_level")
        assert len(demand_col.top_values) > 0


# ---------------------------------------------------------------------------
# Datetime statistics
# ---------------------------------------------------------------------------

class TestDatetimeStatistics:
    def test_request_timestamp_stats(self) -> None:
        df = _make_sample_df()
        result = profile_dataset(df)
        ts_col = next(c for c in result.columns if c.name == "request_timestamp")
        assert ts_col.min_timestamp is not None
        assert ts_col.max_timestamp is not None
        assert ts_col.n_distinct_dates is not None
        assert ts_col.n_distinct_hours is not None


# ---------------------------------------------------------------------------
# Duplicate counts
# ---------------------------------------------------------------------------

class TestDuplicateCounts:
    def test_no_duplicates_in_sample(self) -> None:
        df = _make_sample_df()
        result = profile_dataset(df)
        assert result.duplicate_rows == 0

    def test_duplicates_detected(self) -> None:
        df = _make_sample_df()
        # Add a duplicate row
        df = pd.concat([df, df.iloc[[0]]], ignore_index=True)
        result = profile_dataset(df)
        assert result.duplicate_rows == 1


# ---------------------------------------------------------------------------
# Dataset-level metrics
# ---------------------------------------------------------------------------

class TestDatasetLevelMetrics:
    def test_unique_ride_ids(self) -> None:
        df = _make_sample_df()
        result = profile_dataset(df)
        assert result.unique_ride_ids == 10

    def test_n_cities(self) -> None:
        df = _make_sample_df()
        result = profile_dataset(df)
        assert result.n_cities == 6

    def test_n_riders(self) -> None:
        df = _make_sample_df()
        result = profile_dataset(df)
        assert result.n_riders == 10

    def test_n_drivers(self) -> None:
        df = _make_sample_df()
        result = profile_dataset(df)
        assert result.n_drivers == 7  # 7 unique non-null driver IDs

    def test_time_range(self) -> None:
        df = _make_sample_df()
        result = profile_dataset(df)
        assert "2025" in result.time_range

    def test_total_missing_values(self) -> None:
        df = _make_sample_df()
        result = profile_dataset(df)
        assert result.total_missing_values > 0


# ---------------------------------------------------------------------------
# Business-oriented profiling
# ---------------------------------------------------------------------------

class TestBusinessProfiling:
    def test_rides_by_city(self) -> None:
        df = _make_sample_df()
        result = profile_dataset(df)
        assert "Mumbai" in result.rides_by_city
        assert result.rides_by_city["Mumbai"] == 3

    def test_rides_by_demand_level(self) -> None:
        df = _make_sample_df()
        result = profile_dataset(df)
        assert "high" in result.rides_by_demand_level

    def test_rides_by_outcome(self) -> None:
        df = _make_sample_df()
        result = profile_dataset(df)
        assert "accepted" in result.rides_by_outcome
        assert "completed" in result.rides_by_outcome

    def test_acceptance_rate(self) -> None:
        df = _make_sample_df()
        result = profile_dataset(df)
        assert 0.0 <= result.acceptance_rate <= 1.0

    def test_completion_rate(self) -> None:
        df = _make_sample_df()
        result = profile_dataset(df)
        assert 0.0 <= result.completion_rate <= 1.0

    def test_rider_cancellation_rate(self) -> None:
        df = _make_sample_df()
        result = profile_dataset(df)
        assert 0.0 <= result.rider_cancellation_rate <= 1.0

    def test_surge_stats(self) -> None:
        df = _make_sample_df()
        result = profile_dataset(df)
        assert "min" in result.surge_stats
        assert "max" in result.surge_stats
        assert "mean" in result.surge_stats

    def test_wait_time_stats(self) -> None:
        df = _make_sample_df()
        result = profile_dataset(df)
        assert "min" in result.wait_time_stats
        assert "mean" in result.wait_time_stats
        assert "p95" in result.wait_time_stats


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

class TestSummary:
    def test_summary_contains_key_info(self) -> None:
        df = _make_sample_df()
        result = profile_dataset(df)
        summary = result.summary()
        assert "10 rows" in summary
        assert "20 columns" in summary
        assert "Mumbai" in summary
        assert "Acceptance rate" in summary


# ---------------------------------------------------------------------------
# Save profile report
# ---------------------------------------------------------------------------

class TestSaveProfileReport:
    def test_save_creates_file(self, tmp_path: Path) -> None:
        df = _make_sample_df()
        result = profile_dataset(df)
        output_path = tmp_path / "profile.md"
        save_profile_report(result, output_path)
        assert output_path.exists()

    def test_report_contains_headings(self, tmp_path: Path) -> None:
        df = _make_sample_df()
        result = profile_dataset(df)
        output_path = tmp_path / "profile.md"
        save_profile_report(result, output_path)
        content = output_path.read_text()
        assert "Dataset Overview" in content
        assert "Rides by City" in content
        assert "Column Profiles" in content


# ---------------------------------------------------------------------------
# Generated dataset profiling
# ---------------------------------------------------------------------------

class TestGeneratedDatasetProfiling:
    def test_generated_dataset_profiles(self) -> None:
        """Profile the synthetic dataset from Issue #12."""
        csv_path = Path("/tmp/profile-test.csv")
        if not csv_path.exists():
            pytest.skip("Generated dataset not found")

        df = pd.read_csv(csv_path)
        result = profile_dataset(df)
        assert result.total_rows == 100
        assert result.total_columns == 20
        assert result.unique_ride_ids == 100
        assert result.n_cities == 6
        assert len(result.columns) == 20

    def test_all_columns_have_profiles(self) -> None:
        """Every column should have a profile."""
        csv_path = Path("/tmp/profile-test.csv")
        if not csv_path.exists():
            pytest.skip("Generated dataset not found")

        df = pd.read_csv(csv_path)
        result = profile_dataset(df)
        for col in result.columns:
            assert col.name in df.columns
            assert col.row_count == 100
            assert col.non_null_count + col.null_count == 100
