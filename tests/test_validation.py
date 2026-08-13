"""Tests for dataset source validation."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from roadies.quality.validator import (
    CheckResult,
    ValidationResult,
    validate_dataset,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BASE_COLUMNS = [
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


def _valid_row(**overrides) -> dict:
    """Return a single valid row with optional overrides."""
    row = {
        "ride_id": "R-000001",
        "rider_id": "RDR-001",
        "driver_id": "DRV-001",
        "request_timestamp": "2025-08-01T10:00:00",
        "city": "Mumbai",
        "accepted": True,
        "completed": True,
        "cancelled_by_rider": False,
        "cancelled_by_driver": False,
        "cancellation_reason": None,
        "driver_acceptance_rate": 0.85,
        "driver_rating": 4.5,
        "city_hour_requested_rides": 100,
        "city_hour_available_drivers": 30,
        "demand_level": "high",
        "surge_multiplier": 1.5,
        "base_fare": 120.0,
        "wait_time_minutes": 5.0,
        "trip_duration_minutes": 20.0,
        "trip_distance_km": 8.0,
    }
    row.update(overrides)
    return row


def _make_df(*rows: dict) -> pd.DataFrame:
    """Build a DataFrame from row dicts."""
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Valid dataset
# ---------------------------------------------------------------------------


class TestValidDataset:
    def test_valid_single_row(self) -> None:
        df = _make_df(_valid_row())
        result = validate_dataset(df)
        assert result.passed is True
        assert len(result.errors) == 0

    def test_valid_multiple_rows(self) -> None:
        rows = [
            _valid_row(ride_id="R-000001", city="Mumbai"),
            _valid_row(ride_id="R-000002", city="Delhi", accepted=False, completed=False,
                       cancelled_by_rider=False, cancelled_by_driver=False,
                       driver_id=None, driver_acceptance_rate=None, driver_rating=None,
                       wait_time_minutes=None, trip_duration_minutes=None, trip_distance_km=None,
                       cancellation_reason=None),
            _valid_row(ride_id="R-000003", city="Bangalore", accepted=True, completed=False,
                       cancelled_by_driver=True, cancellation_reason="Vehicle quality",
                       cancelled_by_rider=False, trip_duration_minutes=None, trip_distance_km=None),
        ]
        df = _make_df(*rows)
        result = validate_dataset(df)
        assert result.passed is True

    def test_result_has_row_count(self) -> None:
        df = _make_df(_valid_row(), _valid_row(ride_id="R-000002"))
        result = validate_dataset(df)
        assert result.row_count == 2


# ---------------------------------------------------------------------------
# Empty dataset
# ---------------------------------------------------------------------------


class TestEmptyDataset:
    def test_empty_dataframe_fails(self) -> None:
        df = pd.DataFrame(columns=BASE_COLUMNS)
        result = validate_dataset(df)
        assert result.passed is False
        assert any(c.name == "dataset_not_empty" and not c.passed for c in result.checks)

    def test_empty_returns_zero_row_count(self) -> None:
        df = pd.DataFrame(columns=BASE_COLUMNS)
        result = validate_dataset(df)
        assert result.row_count == 0


# ---------------------------------------------------------------------------
# Missing columns
# ---------------------------------------------------------------------------


class TestMissingColumns:
    def test_missing_required_column_fails(self) -> None:
        row = _valid_row()
        del row["city"]
        df = _make_df(row)
        result = validate_dataset(df)
        assert result.passed is False
        check = next(c for c in result.checks if c.name == "required_columns")
        assert not check.passed
        assert "city" in check.details["missing"]

    def test_multiple_missing_columns_reported(self) -> None:
        row = _valid_row()
        del row["city"]
        del row["demand_level"]
        df = _make_df(row)
        result = validate_dataset(df)
        check = next(c for c in result.checks if c.name == "required_columns")
        assert "city" in check.details["missing"]
        assert "demand_level" in check.details["missing"]


# ---------------------------------------------------------------------------
# Duplicate ride IDs
# ---------------------------------------------------------------------------


class TestDuplicateRideIds:
    def test_duplicate_ride_ids_fail(self) -> None:
        rows = [
            _valid_row(ride_id="R-000001"),
            _valid_row(ride_id="R-000001"),
        ]
        df = _make_df(*rows)
        result = validate_dataset(df)
        assert result.passed is False
        check = next(c for c in result.checks if c.name == "ride_ids_unique")
        assert not check.passed
        assert check.details["unique_count"] == 1
        assert check.details["total_count"] == 2


# ---------------------------------------------------------------------------
# Invalid categorical values
# ---------------------------------------------------------------------------


class TestInvalidCategoricalValues:
    def test_invalid_city_fails(self) -> None:
        df = _make_df(_valid_row(city="London"))
        result = validate_dataset(df)
        check = next(c for c in result.checks if c.name == "valid_cities")
        assert not check.passed
        assert "London" in check.details["invalid"]

    def test_invalid_demand_level_fails(self) -> None:
        df = _make_df(_valid_row(demand_level="extreme"))
        result = validate_dataset(df)
        check = next(c for c in result.checks if c.name == "valid_demand_levels")
        assert not check.passed

    def test_invalid_cancellation_reason_fails(self) -> None:
        df = _make_df(
            _valid_row(
                cancelled_by_rider=True,
                cancelled_by_driver=False,
                cancellation_reason="Mystery reason",
            )
        )
        result = validate_dataset(df)
        check = next(c for c in result.checks if c.name == "valid_cancellation_reasons")
        assert not check.passed

    def test_all_valid_cities_pass(self) -> None:
        from roadies.quality.validator import CITIES
        rows = [_valid_row(ride_id=f"R-{i:06d}", city=c) for i, c in enumerate(CITIES)]
        df = _make_df(*rows)
        result = validate_dataset(df)
        check = next(c for c in result.checks if c.name == "valid_cities")
        assert check.passed


# ---------------------------------------------------------------------------
# Numeric ranges
# ---------------------------------------------------------------------------


class TestNumericRanges:
    def test_surge_too_high_fails(self) -> None:
        df = _make_df(_valid_row(surge_multiplier=10.0))
        result = validate_dataset(df)
        check = next(c for c in result.checks if c.name == "range_surge_multiplier")
        assert not check.passed

    def test_surge_below_minimum_fails(self) -> None:
        df = _make_df(_valid_row(surge_multiplier=0.5))
        result = validate_dataset(df)
        check = next(c for c in result.checks if c.name == "range_surge_multiplier")
        assert not check.passed

    def test_wait_time_negative_fails(self) -> None:
        df = _make_df(_valid_row(wait_time_minutes=-1.0))
        result = validate_dataset(df)
        check = next(c for c in result.checks if c.name == "range_wait_time_minutes")
        assert not check.passed

    def test_base_fare_out_of_range_fails(self) -> None:
        df = _make_df(_valid_row(base_fare=1000.0))
        result = validate_dataset(df)
        check = next(c for c in result.checks if c.name == "range_base_fare")
        assert not check.passed

    def test_acceptance_rate_out_of_range_fails(self) -> None:
        df = _make_df(_valid_row(driver_acceptance_rate=1.5))
        result = validate_dataset(df)
        check = next(c for c in result.checks if c.name == "range_driver_acceptance_rate")
        assert not check.passed

    def test_driver_rating_too_low_fails(self) -> None:
        df = _make_df(_valid_row(driver_rating=0.5))
        result = validate_dataset(df)
        check = next(c for c in result.checks if c.name == "range_driver_rating")
        assert not check.passed


# ---------------------------------------------------------------------------
# Logical cross-checks
# ---------------------------------------------------------------------------


class TestLogicalCrossChecks:
    def test_completed_without_accepted_fails(self) -> None:
        df = _make_df(_valid_row(accepted=False, completed=True))
        result = validate_dataset(df)
        check = next(c for c in result.checks if c.name == "completed_implies_accepted")
        assert not check.passed

    def test_driver_cancel_without_accepted_fails(self) -> None:
        df = _make_df(_valid_row(accepted=False, cancelled_by_driver=True))
        result = validate_dataset(df)
        check = next(c for c in result.checks if c.name == "driver_cancel_implies_accepted")
        assert not check.passed

    def test_rider_cancel_with_completed_fails(self) -> None:
        df = _make_df(_valid_row(cancelled_by_rider=True, completed=True))
        result = validate_dataset(df)
        check = next(c for c in result.checks if c.name == "rider_cancel_implies_not_completed")
        assert not check.passed

    def test_cancellation_reason_when_not_cancelled_fails(self) -> None:
        df = _make_df(
            _valid_row(
                cancelled_by_rider=False,
                cancelled_by_driver=False,
                cancellation_reason="Long wait time",
            )
        )
        result = validate_dataset(df)
        check = next(c for c in result.checks if c.name == "reason_null_when_not_cancelled")
        assert not check.passed

    def test_wait_time_when_not_accepted_fails(self) -> None:
        df = _make_df(_valid_row(accepted=False, wait_time_minutes=5.0))
        result = validate_dataset(df)
        check = next(c for c in result.checks if c.name == "wait_null_when_not_accepted")
        assert not check.passed

    def test_trip_duration_when_not_completed_fails(self) -> None:
        df = _make_df(_valid_row(completed=False, trip_duration_minutes=20.0))
        result = validate_dataset(df)
        check = next(c for c in result.checks if c.name == "trip_duration_minutes_null_when_not_completed")
        assert not check.passed

    def test_trip_distance_when_not_completed_fails(self) -> None:
        df = _make_df(_valid_row(completed=False, trip_distance_km=8.0))
        result = validate_dataset(df)
        check = next(c for c in result.checks if c.name == "trip_distance_km_null_when_not_completed")
        assert not check.passed


# ---------------------------------------------------------------------------
# Multiple failures
# ---------------------------------------------------------------------------


class TestMultipleFailures:
    def test_multiple_failures_reported_together(self) -> None:
        df = _make_df(
            _valid_row(
                city="InvalidCity",
                demand_level="InvalidLevel",
                surge_multiplier=99.0,
            )
        )
        result = validate_dataset(df)
        assert result.passed is False
        failed_names = [c.name for c in result.errors]
        assert "valid_cities" in failed_names
        assert "valid_demand_levels" in failed_names
        assert "range_surge_multiplier" in failed_names

    def test_errors_property_returns_only_failures(self) -> None:
        df = _make_df(_valid_row(city="InvalidCity"))
        result = validate_dataset(df)
        assert all(not c.passed for c in result.errors)


# ---------------------------------------------------------------------------
# ValidationResult
# ---------------------------------------------------------------------------


class TestValidationResult:
    def test_summary_contains_passed(self) -> None:
        df = _make_df(_valid_row())
        result = validate_dataset(df)
        summary = result.summary()
        assert "PASSED" in summary

    def test_summary_contains_failed(self) -> None:
        df = _make_df(_valid_row(city="InvalidCity"))
        result = validate_dataset(df)
        summary = result.summary()
        assert "FAILED" in summary

    def test_checks_list_populated(self) -> None:
        df = _make_df(_valid_row())
        result = validate_dataset(df)
        assert len(result.checks) > 0

    def test_check_result_dataclass(self) -> None:
        cr = CheckResult(name="test", passed=True, message="ok")
        assert cr.name == "test"
        assert cr.passed is True


# ---------------------------------------------------------------------------
# Generated dataset integration
# ---------------------------------------------------------------------------


class TestGeneratedDatasetIntegration:
    def test_generated_dataset_passes(self) -> None:
        """Validate the synthetic dataset from Issue #12."""
        from pathlib import Path

        csv_path = Path("/tmp/val-test-rides.csv")
        if not csv_path.exists():
            pytest.skip("Generated dataset not found")

        df = pd.read_csv(csv_path)
        result = validate_dataset(df)
        assert result.passed is True, result.summary()
        assert result.row_count > 0

    def test_all_checks_pass_on_valid_data(self) -> None:
        """Every check should pass on well-formed data."""
        csv_path = Path("/tmp/val-test-rides.csv")
        if not csv_path.exists():
            pytest.skip("Generated dataset not found")

        df = pd.read_csv(csv_path)
        result = validate_dataset(df)
        for check in result.checks:
            assert check.passed, f"Check '{check.name}' failed: {check.message}"
