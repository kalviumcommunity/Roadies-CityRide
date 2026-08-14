"""Tests for multi-source merging and join validation."""

from __future__ import annotations

import pandas as pd
import pytest

from roadies.quality.join_validation import (
    JoinResult,
    merge_and_validate,
    merge_datasets,
    validate_join,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _rides_df() -> pd.DataFrame:
    return pd.DataFrame({
        "ride_id": ["R-001", "R-002", "R-003", "R-004", "R-005"],
        "city": ["Mumbai", "Delhi", "Mumbai", "Bangalore", "Delhi"],
        "driver_id": ["DRV-01", "DRV-02", "DRV-01", "DRV-03", "DRV-04"],
        "surge_multiplier": [1.0, 1.5, 1.2, 1.0, 1.3],
    })


def _cities_df() -> pd.DataFrame:
    return pd.DataFrame({
        "city": ["Mumbai", "Delhi", "Bangalore"],
        "state": ["Maharashtra", "Delhi", "Karnataka"],
    })


def _drivers_df() -> pd.DataFrame:
    return pd.DataFrame({
        "driver_id": ["DRV-01", "DRV-02", "DRV-03", "DRV-04"],
        "driver_name": ["A", "B", "C", "D"],
    })


def _city_hour_df() -> pd.DataFrame:
    return pd.DataFrame({
        "city": ["Mumbai", "Mumbai", "Delhi", "Delhi"],
        "hour": [9, 10, 9, 10],
        "available_drivers": [10, 12, 8, 9],
        "requested_rides": [50, 60, 30, 35],
    })


# ---------------------------------------------------------------------------
# Valid joins
# ---------------------------------------------------------------------------

class TestValidJoins:
    def test_one_to_one(self) -> None:
        result = merge_and_validate(_rides_df(), _cities_df(), on=["city"], how="left")
        assert result.result_rows == 5
        assert result.unmatched_right == 0
        assert result.row_multiplication is False

    def test_many_to_one(self) -> None:
        result = merge_and_validate(_rides_df(), _drivers_df(), on=["driver_id"], how="left")
        assert result.result_rows == 5
        assert result.unmatched_left == 0

    def test_inner_join(self) -> None:
        rides = _rides_df()
        drivers = pd.DataFrame({
            "driver_id": ["DRV-01", "DRV-02", "DRV-03"],
            "driver_name": ["A", "B", "C"],
        })
        result = merge_and_validate(rides, drivers, on=["driver_id"], how="inner")
        assert result.result_rows == 4  # DRV-04 not in drivers


# ---------------------------------------------------------------------------
# Unmatched keys
# ---------------------------------------------------------------------------

class TestUnmatched:
    def test_unmatched_right(self) -> None:
        rides = _rides_df()
        cities = pd.DataFrame({"city": ["Mumbai"], "state": ["Maharashtra"]})
        result = merge_and_validate(rides, cities, on=["city"], how="left")
        assert result.unmatched_right >= 0

    def test_unmatched_left_inner(self) -> None:
        rides = _rides_df()
        drivers = pd.DataFrame({"driver_id": ["DRV-01"], "name": ["A"]})
        result = merge_and_validate(rides, drivers, on=["driver_id"], how="inner")
        assert result.unmatched_left >= 0


# ---------------------------------------------------------------------------
# Duplicate keys
# ---------------------------------------------------------------------------

class TestDuplicates:
    def test_duplicate_keys_detected(self) -> None:
        right = pd.DataFrame({
            "city": ["Mumbai", "Mumbai", "Delhi"],
            "val": [1, 2, 3],
        })
        result = merge_and_validate(_rides_df(), right, on=["city"], how="left")
        assert result.duplicate_keys_right > 0
        assert result.row_multiplication is True


# ---------------------------------------------------------------------------
# Row multiplication
# ---------------------------------------------------------------------------

class TestRowMultiplication:
    def test_multiplication_detected(self) -> None:
        right = pd.DataFrame({
            "city": ["Mumbai", "Mumbai", "Delhi", "Delhi", "Bangalore"],
            "val": [1, 2, 3, 4, 5],
        })
        result = merge_and_validate(_rides_df(), right, on=["city"], how="left")
        assert result.row_multiplication is True
        assert result.result_rows > 5

    def test_no_multiplication(self) -> None:
        result = merge_and_validate(_rides_df(), _cities_df(), on=["city"], how="left")
        assert result.row_multiplication is False


# ---------------------------------------------------------------------------
# Match percentage
# ---------------------------------------------------------------------------

class TestMatchPercentage:
    def test_full_match(self) -> None:
        result = merge_and_validate(_rides_df(), _cities_df(), on=["city"], how="left")
        assert result.match_pct == 100.0

    def test_partial_match(self) -> None:
        rides = _rides_df()
        drivers = pd.DataFrame({"driver_id": ["DRV-01"], "name": ["A"]})
        result = merge_and_validate(rides, drivers, on=["driver_id"], how="inner")
        assert 0 <= result.match_pct <= 100


# ---------------------------------------------------------------------------
# Simple merge_datasets
# ---------------------------------------------------------------------------

class TestMergeDatasets:
    def test_returns_dataframe(self) -> None:
        merged = merge_datasets(_rides_df(), _cities_df(), on=["city"])
        assert len(merged) == 5
        assert "state" in merged.columns


# ---------------------------------------------------------------------------
# validate_join
# ---------------------------------------------------------------------------

class TestValidateJoin:
    def test_returns_join_result(self) -> None:
        result = validate_join(_rides_df(), _cities_df(), on=["city"])
        assert isinstance(result, JoinResult)


# ---------------------------------------------------------------------------
# City-hour contextual join
# ---------------------------------------------------------------------------

class TestCityHourJoin:
    def test_city_hour_join(self) -> None:
        rides = pd.DataFrame({
            "ride_id": ["R-001", "R-002"],
            "city": ["Mumbai", "Delhi"],
            "hour": [9, 9],
        })
        result = merge_and_validate(rides, _city_hour_df(), on=["city", "hour"], how="left")
        assert result.result_rows == 2
        assert result.match_pct == 100.0
