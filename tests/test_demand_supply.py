"""Tests for demand and supply feature engineering."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from roadies.features.demand_supply import (
    FeatureEngineeringReport,
    engineer_demand_supply_features,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _demand_df(req: int, avail: int) -> pd.DataFrame:
    return pd.DataFrame({
        "ride_id": ["R-001"],
        "city_hour_requested_rides": [req],
        "city_hour_available_drivers": [avail],
    })


# ---------------------------------------------------------------------------
# Demand/supply calculations
# ---------------------------------------------------------------------------

class TestCalculations:
    def test_demand_supply_ratio(self) -> None:
        df = _demand_df(50, 10)
        result, _ = engineer_demand_supply_features(df)
        assert result["demand_supply_ratio"].iloc[0] == 5.0

    def test_supply_pressure(self) -> None:
        df = _demand_df(50, 10)
        result, _ = engineer_demand_supply_features(df)
        assert result["supply_pressure"].iloc[0] == 0.2

    def test_demand_intensity(self) -> None:
        df = _demand_df(50, 10)
        result, _ = engineer_demand_supply_features(df)
        assert result["demand_intensity"].iloc[0] == pytest.approx(50 / 60)

    def test_driver_availability_rate(self) -> None:
        df = _demand_df(50, 10)
        result, _ = engineer_demand_supply_features(df)
        assert result["driver_availability_rate"].iloc[0] == pytest.approx(10 / 60)

    def test_demand_surplus(self) -> None:
        df = _demand_df(50, 10)
        result, _ = engineer_demand_supply_features(df)
        assert result["demand_surplus"].iloc[0] == 40

    def test_surge_pressure(self) -> None:
        df = _demand_df(50, 10)
        result, _ = engineer_demand_supply_features(df)
        assert result["surge_pressure"].iloc[0] == pytest.approx(0.8)


# ---------------------------------------------------------------------------
# Zero-supply handling
# ---------------------------------------------------------------------------

class TestZeroSupply:
    def test_zero_supply_ratio(self) -> None:
        df = _demand_df(50, 0)
        result, _ = engineer_demand_supply_features(df)
        assert np.isnan(result["demand_supply_ratio"].iloc[0])

    def test_zero_supply_intensity(self) -> None:
        df = _demand_df(50, 0)
        result, _ = engineer_demand_supply_features(df)
        assert result["demand_intensity"].iloc[0] == 1.0

    def test_zero_request_surge_pressure(self) -> None:
        df = _demand_df(0, 10)
        result, _ = engineer_demand_supply_features(df)
        assert np.isnan(result["surge_pressure"].iloc[0])


# ---------------------------------------------------------------------------
# Expected ranges
# ---------------------------------------------------------------------------

class TestRanges:
    def test_demand_intensity_range(self) -> None:
        df = pd.DataFrame({
            "ride_id": [f"R-{i:03d}" for i in range(10)],
            "city_hour_requested_rides": [10, 50, 0, 100, 5, 20, 80, 30, 60, 40],
            "city_hour_available_drivers": [10, 10, 10, 10, 10, 10, 10, 10, 10, 10],
        })
        result, _ = engineer_demand_supply_features(df)
        assert (result["demand_intensity"] >= 0).all()
        assert (result["demand_intensity"] <= 1).all()

    def test_surge_pressure_range(self) -> None:
        df = pd.DataFrame({
            "ride_id": [f"R-{i:03d}" for i in range(5)],
            "city_hour_requested_rides": [10, 50, 0, 100, 5],
            "city_hour_available_drivers": [10, 10, 10, 10, 10],
        })
        result, _ = engineer_demand_supply_features(df)
        valid = result["surge_pressure"].dropna()
        assert (valid >= 0).all()
        assert (valid <= 1).all()


# ---------------------------------------------------------------------------
# Preservation of raw columns
# ---------------------------------------------------------------------------

class TestPreservation:
    def test_raw_columns_preserved(self) -> None:
        df = _demand_df(50, 10)
        result, _ = engineer_demand_supply_features(df)
        assert "city_hour_requested_rides" in result.columns
        assert "city_hour_available_drivers" in result.columns
        assert result["city_hour_requested_rides"].iloc[0] == 50


# ---------------------------------------------------------------------------
# Feature column creation
# ---------------------------------------------------------------------------

class TestFeatureColumns:
    def test_all_features_created(self) -> None:
        df = _demand_df(50, 10)
        result, _ = engineer_demand_supply_features(df)
        expected = [
            "demand_supply_ratio", "supply_pressure", "demand_intensity",
            "driver_availability_rate", "demand_surplus", "surge_pressure",
        ]
        for col in expected:
            assert col in result.columns


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

class TestReport:
    def test_report_created(self) -> None:
        df = _demand_df(50, 10)
        _, report = engineer_demand_supply_features(df)
        assert isinstance(report, FeatureEngineeringReport)
        assert len(report.features_created) == 6


# ---------------------------------------------------------------------------
# Generated dataset integration
# ---------------------------------------------------------------------------

class TestGeneratedDataset:
    def test_generated_dataset(self) -> None:
        csv_path = Path("/tmp/profile-test.csv")
        if not csv_path.exists():
            pytest.skip("Generated dataset not found")
        df = pd.read_csv(csv_path)
        result, report = engineer_demand_supply_features(df)
        assert report.rows_processed == len(df)
        assert len(report.features_created) == 6
        assert "demand_supply_ratio" in result.columns
