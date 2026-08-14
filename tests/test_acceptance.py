"""Tests for driver acceptance behaviour feature engineering."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from roadies.features.acceptance import (
    ACCEPTANCE_RATE_BASELINE,
    AcceptanceFeatureReport,
    engineer_acceptance_features,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _acceptance_df(
    accepted: bool = True,
    dar: float = 0.85,
    driver_id: str | None = "DRV-001",
) -> pd.DataFrame:
    return pd.DataFrame({
        "ride_id": ["R-001"],
        "accepted": [accepted],
        "driver_id": [driver_id],
        "driver_acceptance_rate": [dar],
    })


# ---------------------------------------------------------------------------
# Accepted ride behaviour
# ---------------------------------------------------------------------------

class TestAccepted:
    def test_was_accepted_true(self) -> None:
        df = _acceptance_df(accepted=True)
        result, _ = engineer_acceptance_features(df)
        assert result["was_accepted"].iloc[0] == True
        assert result["was_not_accepted"].iloc[0] == False


# ---------------------------------------------------------------------------
# Rejected/unaccepted ride behaviour
# ---------------------------------------------------------------------------

class TestNotAccepted:
    def test_was_not_accepted(self) -> None:
        df = _acceptance_df(accepted=False)
        result, _ = engineer_acceptance_features(df)
        assert result["was_accepted"].iloc[0] == False
        assert result["was_not_accepted"].iloc[0] == True


# ---------------------------------------------------------------------------
# Acceptance rate deviation
# ---------------------------------------------------------------------------

class TestDeviation:
    def test_above_baseline(self) -> None:
        df = _acceptance_df(dar=0.90)
        result, _ = engineer_acceptance_features(df)
        assert result["acceptance_rate_deviation"].iloc[0] == pytest.approx(0.10)

    def test_below_baseline(self) -> None:
        df = _acceptance_df(dar=0.70)
        result, _ = engineer_acceptance_features(df)
        assert result["acceptance_rate_deviation"].iloc[0] == pytest.approx(-0.10)

    def test_at_baseline(self) -> None:
        df = _acceptance_df(dar=0.80)
        result, _ = engineer_acceptance_features(df)
        assert result["acceptance_rate_deviation"].iloc[0] == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Acceptance rate band
# ---------------------------------------------------------------------------

class TestBand:
    def test_well_above(self) -> None:
        df = _acceptance_df(dar=0.95)
        result, _ = engineer_acceptance_features(df)
        assert result["acceptance_rate_band"].iloc[0] == "well_above"

    def test_above(self) -> None:
        df = _acceptance_df(dar=0.87)
        result, _ = engineer_acceptance_features(df)
        assert result["acceptance_rate_band"].iloc[0] == "above"

    def test_near_baseline(self) -> None:
        df = _acceptance_df(dar=0.82)
        result, _ = engineer_acceptance_features(df)
        assert result["acceptance_rate_band"].iloc[0] == "near_baseline"

    def test_below(self) -> None:
        df = _acceptance_df(dar=0.73)
        result, _ = engineer_acceptance_features(df)
        assert result["acceptance_rate_band"].iloc[0] == "below"

    def test_well_below(self) -> None:
        df = _acceptance_df(dar=0.50)
        result, _ = engineer_acceptance_features(df)
        assert result["acceptance_rate_band"].iloc[0] == "well_below"


# ---------------------------------------------------------------------------
# has_driver
# ---------------------------------------------------------------------------

class TestHasDriver:
    def test_has_driver(self) -> None:
        df = _acceptance_df(driver_id="DRV-001")
        result, _ = engineer_acceptance_features(df)
        assert result["has_driver"].iloc[0] == True

    def test_no_driver(self) -> None:
        df = _acceptance_df(driver_id=None)
        result, _ = engineer_acceptance_features(df)
        assert result["has_driver"].iloc[0] == False


# ---------------------------------------------------------------------------
# Missing values
# ---------------------------------------------------------------------------

class TestMissing:
    def test_null_acceptance_rate(self) -> None:
        df = pd.DataFrame({
            "ride_id": ["R-001"],
            "accepted": [True],
            "driver_id": ["DRV-001"],
            "driver_acceptance_rate": [None],
        })
        result, _ = engineer_acceptance_features(df)
        assert result["acceptance_rate_band"].iloc[0] == "unknown"
        assert np.isnan(result["acceptance_rate_deviation"].iloc[0])


# ---------------------------------------------------------------------------
# Preservation
# ---------------------------------------------------------------------------

class TestPreservation:
    def test_raw_columns_preserved(self) -> None:
        df = _acceptance_df()
        result, _ = engineer_acceptance_features(df)
        assert "accepted" in result.columns
        assert "driver_acceptance_rate" in result.columns
        assert "driver_id" in result.columns


# ---------------------------------------------------------------------------
# Feature columns
# ---------------------------------------------------------------------------

class TestFeatureColumns:
    def test_all_created(self) -> None:
        df = _acceptance_df()
        result, _ = engineer_acceptance_features(df)
        expected = [
            "was_accepted", "was_not_accepted", "acceptance_rate_deviation",
            "acceptance_rate_band", "has_driver",
        ]
        for col in expected:
            assert col in result.columns


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

class TestReport:
    def test_report_created(self) -> None:
        df = _acceptance_df()
        _, report = engineer_acceptance_features(df)
        assert isinstance(report, AcceptanceFeatureReport)
        assert report.baseline == ACCEPTANCE_RATE_BASELINE
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
        result, report = engineer_acceptance_features(df)
        assert report.rows_processed == len(df)
        assert len(report.features_created) == 5
