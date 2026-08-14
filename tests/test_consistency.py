"""Tests for data consistency and validation rules engine."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from roadies.quality.consistency import (
    ConsistencyReport,
    validate_consistency,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _valid_df(n: int = 5) -> pd.DataFrame:
    """Create a valid baseline DataFrame."""
    return pd.DataFrame({
        "ride_id": [f"R-{i:06d}" for i in range(1, n + 1)],
        "completed": [True, False, True, False, True],
        "accepted": [True, True, True, False, True],
        "cancelled_by_rider": [False, False, False, True, False],
        "cancelled_by_driver": [False, False, False, False, False],
        "cancellation_reason": [None, None, None, "Changed mind", None],
        "driver_rating": [4.5, 4.0, None, None, 3.5],
        "wait_time_minutes": [5.0, 3.0, 8.0, 2.0, 6.0],
        "trip_duration_minutes": [20.0, 0.0, 25.0, 0.0, 15.0],
        "trip_distance_km": [10.0, 0.0, 12.0, 0.0, 8.0],
        "surge_multiplier": [1.0, 1.5, 1.2, 1.0, 1.3],
        "base_fare": [100.0, 150.0, 120.0, 80.0, 110.0],
        "city_hour_requested_rides": [50, 30, 45, 20, 60],
        "city_hour_available_drivers": [10, 8, 12, 5, 15],
    })


# ---------------------------------------------------------------------------
# Ride outcome consistency
# ---------------------------------------------------------------------------

class TestRideOutcome:
    def test_completed_no_driver(self) -> None:
        df = _valid_df()
        df.loc[0, "accepted"] = False  # completed but not accepted
        report = validate_consistency(df)
        r = next(x for x in report.rule_results if x.rule_id == "ride_outcome_01")
        assert r.violation_count == 1

    def test_completed_with_rider_cancel(self) -> None:
        df = _valid_df()
        df.loc[0, "cancelled_by_rider"] = True
        report = validate_consistency(df)
        r = next(x for x in report.rule_results if x.rule_id == "ride_outcome_02")
        assert r.violation_count == 1

    def test_completed_with_driver_cancel(self) -> None:
        df = _valid_df()
        df.loc[0, "cancelled_by_driver"] = True
        report = validate_consistency(df)
        r = next(x for x in report.rule_results if x.rule_id == "ride_outcome_03")
        assert r.violation_count == 1

    def test_cancelled_no_reason(self) -> None:
        df = _valid_df()
        df.loc[3, "cancellation_reason"] = None
        report = validate_consistency(df)
        r = next(x for x in report.rule_results if x.rule_id == "ride_outcome_04")
        assert r.violation_count == 1

    def test_no_cancel_has_reason(self) -> None:
        df = _valid_df()
        df.loc[0, "cancellation_reason"] = "Other"
        report = validate_consistency(df)
        r = next(x for x in report.rule_results if x.rule_id == "ride_outcome_05")
        assert r.violation_count == 1


# ---------------------------------------------------------------------------
# Driver consistency
# ---------------------------------------------------------------------------

class TestDriver:
    def test_rating_without_driver(self) -> None:
        df = _valid_df()
        df.loc[0, "accepted"] = False
        report = validate_consistency(df)
        r = next(x for x in report.rule_results if x.rule_id == "driver_01")
        assert r.violation_count == 1


# ---------------------------------------------------------------------------
# Time consistency
# ---------------------------------------------------------------------------

class TestTime:
    def test_negative_wait_time(self) -> None:
        df = _valid_df()
        df.loc[0, "wait_time_minutes"] = -1.0
        report = validate_consistency(df)
        r = next(x for x in report.rule_results if x.rule_id == "time_01")
        assert r.violation_count == 1

    def test_negative_trip_duration(self) -> None:
        df = _valid_df()
        df.loc[0, "trip_duration_minutes"] = -5.0
        report = validate_consistency(df)
        r = next(x for x in report.rule_results if x.rule_id == "time_02")
        assert r.violation_count == 1

    def test_negative_distance(self) -> None:
        df = _valid_df()
        df.loc[0, "trip_distance_km"] = -2.0
        report = validate_consistency(df)
        r = next(x for x in report.rule_results if x.rule_id == "time_03")
        assert r.violation_count == 1


# ---------------------------------------------------------------------------
# Pricing consistency
# ---------------------------------------------------------------------------

class TestPricing:
    def test_surge_too_high(self) -> None:
        df = _valid_df()
        df.loc[0, "surge_multiplier"] = 10.0
        report = validate_consistency(df)
        r = next(x for x in report.rule_results if x.rule_id == "pricing_01")
        assert r.violation_count == 1

    def test_surge_too_low(self) -> None:
        df = _valid_df()
        df.loc[0, "surge_multiplier"] = 0.5
        report = validate_consistency(df)
        r = next(x for x in report.rule_results if x.rule_id == "pricing_01")
        assert r.violation_count == 1

    def test_negative_fare(self) -> None:
        df = _valid_df()
        df.loc[0, "base_fare"] = -10.0
        report = validate_consistency(df)
        r = next(x for x in report.rule_results if x.rule_id == "pricing_02")
        assert r.violation_count == 1


# ---------------------------------------------------------------------------
# Demand/supply consistency
# ---------------------------------------------------------------------------

class TestDemand:
    def test_negative_requested(self) -> None:
        df = _valid_df()
        df.loc[0, "city_hour_requested_rides"] = -5
        report = validate_consistency(df)
        r = next(x for x in report.rule_results if x.rule_id == "demand_01")
        assert r.violation_count == 1

    def test_negative_available(self) -> None:
        df = _valid_df()
        df.loc[0, "city_hour_available_drivers"] = -1
        report = validate_consistency(df)
        r = next(x for x in report.rule_results if x.rule_id == "demand_02")
        assert r.violation_count == 1


# ---------------------------------------------------------------------------
# Multiple violations
# ---------------------------------------------------------------------------

class TestMultipleViolations:
    def test_multiple_rules_fail(self) -> None:
        df = _valid_df()
        df.loc[0, "accepted"] = False
        df.loc[0, "wait_time_minutes"] = -1.0
        report = validate_consistency(df)
        failed = [r for r in report.rule_results if not r.passed]
        assert len(failed) >= 2


# ---------------------------------------------------------------------------
# Valid records
# ---------------------------------------------------------------------------

class TestValidRecords:
    def test_valid_df_passes_all(self) -> None:
        df = _valid_df()
        report = validate_consistency(df)
        assert report.rules_failed == 0


# ---------------------------------------------------------------------------
# Generated dataset integration
# ---------------------------------------------------------------------------

class TestGeneratedDataset:
    def test_generated_dataset(self) -> None:
        csv_path = Path("/tmp/profile-test.csv")
        if not csv_path.exists():
            pytest.skip("Generated dataset not found")
        df = pd.read_csv(csv_path)
        report = validate_consistency(df)
        assert report.total_rows == len(df)
        assert report.rules_evaluated > 0
