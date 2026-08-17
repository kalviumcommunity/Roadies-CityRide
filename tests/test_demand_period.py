"""Tests for high-demand period classification."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from roadies.features.demand_period import (
    HIGH_DEMAND_PERCENTILE,
    DemandPeriodReport,
    classify_high_demand,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _demand_df(requests: list[int]) -> pd.DataFrame:
    return pd.DataFrame({
        "ride_id": [f"R-{i:03d}" for i in range(len(requests))],
        "city_hour_requested_rides": requests,
    })


# ---------------------------------------------------------------------------
# 80th-percentile calculation
# ---------------------------------------------------------------------------

class TestPercentile:
    def test_threshold_calculation(self) -> None:
        df = _demand_df([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
        _, report = classify_high_demand(df)
        assert report.threshold_value == pytest.approx(82.0)

    def test_percentile_column_created(self) -> None:
        df = _demand_df([10, 20, 30, 40, 50])
        result, _ = classify_high_demand(df)
        assert "demand_percentile" in result.columns


# ---------------------------------------------------------------------------
# Values below threshold
# ---------------------------------------------------------------------------

class TestBelowThreshold:
    def test_below_not_high(self) -> None:
        df = _demand_df([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
        result, _ = classify_high_demand(df)
        # First value (10) should not be high demand
        assert result["is_high_demand"].iloc[0] == False


# ---------------------------------------------------------------------------
# Values at/above threshold
# ---------------------------------------------------------------------------

class TestAtAboveThreshold:
    def test_above_is_high(self) -> None:
        df = _demand_df([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
        result, _ = classify_high_demand(df)
        # Last value (100) should be high demand
        assert result["is_high_demand"].iloc[9] == True


# ---------------------------------------------------------------------------
# Demand period category
# ---------------------------------------------------------------------------

class TestDemandPeriod:
    def test_low_period(self) -> None:
        df = _demand_df([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
        result, _ = classify_high_demand(df)
        assert result["demand_period"].iloc[0] == "low"

    def test_high_period(self) -> None:
        df = _demand_df([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
        result, _ = classify_high_demand(df)
        assert result["demand_period"].iloc[9] == "high"


# ---------------------------------------------------------------------------
# Small datasets
# ---------------------------------------------------------------------------

class TestSmallDataset:
    def test_single_row(self) -> None:
        df = _demand_df([50])
        result, report = classify_high_demand(df)
        assert report.rows_processed == 1
        assert "is_high_demand" in result.columns

    def test_two_rows(self) -> None:
        df = _demand_df([10, 100])
        result, report = classify_high_demand(df)
        assert report.rows_processed == 2


# ---------------------------------------------------------------------------
# Constant demand
# ---------------------------------------------------------------------------

class TestConstantDemand:
    def test_all_same(self) -> None:
        df = _demand_df([50, 50, 50, 50, 50])
        result, report = classify_high_demand(df)
        # All values equal the threshold, so all are high demand
        assert result["is_high_demand"].all()


# ---------------------------------------------------------------------------
# Missing values
# ---------------------------------------------------------------------------

class TestMissing:
    def test_null_demand(self) -> None:
        df = pd.DataFrame({
            "ride_id": ["R-001"],
            "city_hour_requested_rides": [None],
        })
        result, report = classify_high_demand(df)
        assert report.rows_processed == 1
        assert "is_high_demand" in result.columns


# ---------------------------------------------------------------------------
# Preservation
# ---------------------------------------------------------------------------

class TestPreservation:
    def test_raw_columns_preserved(self) -> None:
        df = _demand_df([10, 20, 30])
        result, _ = classify_high_demand(df)
        assert "city_hour_requested_rides" in result.columns
        assert result["city_hour_requested_rides"].iloc[0] == 10


# ---------------------------------------------------------------------------
# Feature columns
# ---------------------------------------------------------------------------

class TestFeatureColumns:
    def test_all_created(self) -> None:
        df = _demand_df([10, 20, 30])
        result, _ = classify_high_demand(df)
        expected = ["demand_percentile", "is_high_demand", "demand_period"]
        for col in expected:
            assert col in result.columns


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

class TestReport:
    def test_report_created(self) -> None:
        df = _demand_df([10, 20, 30, 40, 50])
        _, report = classify_high_demand(df)
        assert isinstance(report, DemandPeriodReport)
        assert report.percentile_threshold == HIGH_DEMAND_PERCENTILE
        assert report.high_demand_count >= 0


# ---------------------------------------------------------------------------
# Generated dataset integration
# ---------------------------------------------------------------------------

class TestGeneratedDataset:
    def test_generated_dataset(self) -> None:
        csv_path = Path("/tmp/profile-test.csv")
        if not csv_path.exists():
            pytest.skip("Generated dataset not found")
        df = pd.read_csv(csv_path)
        result, report = classify_high_demand(df)
        assert report.rows_processed == len(df)
        assert report.high_demand_count > 0
        assert report.high_demand_pct > 0
