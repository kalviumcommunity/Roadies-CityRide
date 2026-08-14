"""Tests for surge pricing feature engineering."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from roadies.features.surge import (
    SurgeFeatureReport,
    engineer_surge_features,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _surge_df(surge: float, dsr: float = 2.0) -> pd.DataFrame:
    return pd.DataFrame({
        "ride_id": ["R-001"],
        "surge_multiplier": [surge],
        "demand_supply_ratio": [dsr],
    })


# ---------------------------------------------------------------------------
# Baseline handling
# ---------------------------------------------------------------------------

class TestBaseline:
    def test_no_surge_deviation(self) -> None:
        df = _surge_df(1.0)
        result, _ = engineer_surge_features(df)
        assert result["surge_deviation"].iloc[0] == 0.0

    def test_no_surge_intensity(self) -> None:
        df = _surge_df(1.0)
        result, _ = engineer_surge_features(df)
        assert result["surge_intensity"].iloc[0] == 0.0


# ---------------------------------------------------------------------------
# Surge deviation
# ---------------------------------------------------------------------------

class TestDeviation:
    def test_positive_deviation(self) -> None:
        df = _surge_df(2.0)
        result, _ = engineer_surge_features(df)
        assert result["surge_deviation"].iloc[0] == 1.0


# ---------------------------------------------------------------------------
# Surge intensity
# ---------------------------------------------------------------------------

class TestIntensity:
    def test_max_intensity(self) -> None:
        df = _surge_df(5.0)
        result, _ = engineer_surge_features(df)
        assert result["surge_intensity"].iloc[0] == 1.0

    def test_half_intensity(self) -> None:
        df = _surge_df(3.0)
        result, _ = engineer_surge_features(df)
        assert result["surge_intensity"].iloc[0] == 0.5


# ---------------------------------------------------------------------------
# Surge categorisation
# ---------------------------------------------------------------------------

class TestCategorisation:
    def test_no_surge(self) -> None:
        df = _surge_df(1.0)
        result, _ = engineer_surge_features(df)
        assert result["surge_category"].iloc[0] == "no_surge"

    def test_low_surge(self) -> None:
        df = _surge_df(1.3)
        result, _ = engineer_surge_features(df)
        assert result["surge_category"].iloc[0] == "low"

    def test_moderate_surge(self) -> None:
        df = _surge_df(2.0)
        result, _ = engineer_surge_features(df)
        assert result["surge_category"].iloc[0] == "moderate"

    def test_high_surge(self) -> None:
        df = _surge_df(3.0)
        result, _ = engineer_surge_features(df)
        assert result["surge_category"].iloc[0] == "high"


# ---------------------------------------------------------------------------
# Threshold boundary
# ---------------------------------------------------------------------------

class TestThresholds:
    def test_boundary_1_5(self) -> None:
        df = _surge_df(1.5)
        result, _ = engineer_surge_features(df)
        assert result["surge_category"].iloc[0] == "low"

    def test_boundary_2_5(self) -> None:
        df = _surge_df(2.5)
        result, _ = engineer_surge_features(df)
        assert result["surge_category"].iloc[0] == "moderate"


# ---------------------------------------------------------------------------
# has_surge
# ---------------------------------------------------------------------------

class TestHasSurge:
    def test_true(self) -> None:
        df = _surge_df(1.5)
        result, _ = engineer_surge_features(df)
        assert result["has_surge"].iloc[0] == True

    def test_false(self) -> None:
        df = _surge_df(1.0)
        result, _ = engineer_surge_features(df)
        assert result["has_surge"].iloc[0] == False


# ---------------------------------------------------------------------------
# Missing values
# ---------------------------------------------------------------------------

class TestMissing:
    def test_null_surge(self) -> None:
        df = pd.DataFrame({
            "ride_id": ["R-001"],
            "surge_multiplier": [None],
            "demand_supply_ratio": [2.0],
        })
        result, _ = engineer_surge_features(df)
        assert np.isnan(result["surge_deviation"].iloc[0])


# ---------------------------------------------------------------------------
# Preservation
# ---------------------------------------------------------------------------

class TestPreservation:
    def test_raw_columns_preserved(self) -> None:
        df = _surge_df(1.5)
        result, _ = engineer_surge_features(df)
        assert result["surge_multiplier"].iloc[0] == 1.5


# ---------------------------------------------------------------------------
# Feature columns
# ---------------------------------------------------------------------------

class TestFeatureColumns:
    def test_all_created(self) -> None:
        df = _surge_df(1.5)
        result, _ = engineer_surge_features(df)
        expected = [
            "surge_deviation", "surge_intensity", "surge_category",
            "has_surge", "surge_to_demand_ratio",
        ]
        for col in expected:
            assert col in result.columns


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

class TestReport:
    def test_report_created(self) -> None:
        df = _surge_df(1.5)
        _, report = engineer_surge_features(df)
        assert isinstance(report, SurgeFeatureReport)
        assert report.baseline == 1.0
        assert len(report.features_created) == 5


# ---------------------------------------------------------------------------
# Generated dataset integration
# ---------------------------------------------------------------------------

class TestGeneratedDataset:
    def test_generated_dataset(self) -> None:
        csv_path = Path("/tmp/profile-test.csv")
        if not csv_path.exists():
            pytest.skip("Generated dataset not found")
        df = pd.read_csv(csv_path)
        # Add demand_supply_ratio if not present
        if "demand_supply_ratio" not in df.columns:
            from roadies.features.demand_supply import engineer_demand_supply_features
            df, _ = engineer_demand_supply_features(df)
        result, report = engineer_surge_features(df)
        assert report.rows_processed == len(df)
        assert len(report.features_created) == 5
