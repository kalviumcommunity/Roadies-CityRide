"""Tests for rider experience feature engineering."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from roadies.features.experience import (
    ExperienceFeatureReport,
    engineer_experience_features,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _exp_df(
    completed: bool = True,
    accepted: bool = True,
    rider_cancel: bool = False,
    driver_cancel: bool = False,
    wait: float | None = 5.0,
    surge: float = 1.0,
) -> pd.DataFrame:
    return pd.DataFrame({
        "ride_id": ["R-001"],
        "completed": [completed],
        "accepted": [accepted],
        "cancelled_by_rider": [rider_cancel],
        "cancelled_by_driver": [driver_cancel],
        "wait_time_minutes": [wait],
        "surge_multiplier": [surge],
    })


# ---------------------------------------------------------------------------
# Wait-time classification
# ---------------------------------------------------------------------------

class TestWaitTime:
    def test_low(self) -> None:
        df = _exp_df(wait=3.0)
        result, _ = engineer_experience_features(df)
        assert result["wait_time_severity"].iloc[0] == "low"

    def test_moderate(self) -> None:
        df = _exp_df(wait=10.0)
        result, _ = engineer_experience_features(df)
        assert result["wait_time_severity"].iloc[0] == "moderate"

    def test_high(self) -> None:
        df = _exp_df(wait=20.0)
        result, _ = engineer_experience_features(df)
        assert result["wait_time_severity"].iloc[0] == "high"

    def test_severe(self) -> None:
        df = _exp_df(wait=45.0)
        result, _ = engineer_experience_features(df)
        assert result["wait_time_severity"].iloc[0] == "severe"

    def test_null_wait(self) -> None:
        df = _exp_df(wait=None)
        result, _ = engineer_experience_features(df)
        assert result["wait_time_severity"].iloc[0] == "unknown"


# ---------------------------------------------------------------------------
# Completion status
# ---------------------------------------------------------------------------

class TestCompletion:
    def test_completed(self) -> None:
        df = _exp_df(completed=True)
        result, _ = engineer_experience_features(df)
        assert result["ride_completed"].iloc[0] == True
        assert result["ride_not_completed"].iloc[0] == False

    def test_not_completed(self) -> None:
        df = _exp_df(completed=False)
        result, _ = engineer_experience_features(df)
        assert result["ride_completed"].iloc[0] == False
        assert result["ride_not_completed"].iloc[0] == True


# ---------------------------------------------------------------------------
# Cancellation type
# ---------------------------------------------------------------------------

class TestCancellation:
    def test_no_cancellation(self) -> None:
        df = _exp_df()
        result, _ = engineer_experience_features(df)
        assert result["cancellation_type"].iloc[0] == "none"

    def test_rider_cancel(self) -> None:
        df = _exp_df(rider_cancel=True)
        result, _ = engineer_experience_features(df)
        assert result["cancellation_type"].iloc[0] == "rider"

    def test_driver_cancel(self) -> None:
        df = _exp_df(driver_cancel=True)
        result, _ = engineer_experience_features(df)
        assert result["cancellation_type"].iloc[0] == "driver"


# ---------------------------------------------------------------------------
# Surge exposure
# ---------------------------------------------------------------------------

class TestSurgeExposure:
    def test_no_surge(self) -> None:
        df = _exp_df(surge=1.0)
        result, _ = engineer_experience_features(df)
        assert result["surge_exposure"].iloc[0] == "none"

    def test_low_surge(self) -> None:
        df = _exp_df(surge=1.3)
        result, _ = engineer_experience_features(df)
        assert result["surge_exposure"].iloc[0] == "low"

    def test_moderate_surge(self) -> None:
        df = _exp_df(surge=2.0)
        result, _ = engineer_experience_features(df)
        assert result["surge_exposure"].iloc[0] == "moderate"

    def test_high_surge(self) -> None:
        df = _exp_df(surge=3.0)
        result, _ = engineer_experience_features(df)
        assert result["surge_exposure"].iloc[0] == "high"


# ---------------------------------------------------------------------------
# Experience classification
# ---------------------------------------------------------------------------

class TestExperienceStatus:
    def test_completed_good(self) -> None:
        df = _exp_df(completed=True, wait=3.0, surge=1.0)
        result, _ = engineer_experience_features(df)
        assert result["experience_status"].iloc[0] == "completed_good"

    def test_completed_elevated_wait(self) -> None:
        df = _exp_df(completed=True, wait=20.0, surge=1.0)
        result, _ = engineer_experience_features(df)
        assert result["experience_status"].iloc[0] == "completed_elevated_wait"

    def test_completed_high_surge(self) -> None:
        df = _exp_df(completed=True, wait=3.0, surge=3.0)
        result, _ = engineer_experience_features(df)
        assert result["experience_status"].iloc[0] == "completed_high_surge"

    def test_rider_cancelled(self) -> None:
        df = _exp_df(rider_cancel=True)
        result, _ = engineer_experience_features(df)
        assert result["experience_status"].iloc[0] == "rider_cancelled"

    def test_driver_cancelled(self) -> None:
        df = _exp_df(driver_cancel=True)
        result, _ = engineer_experience_features(df)
        assert result["experience_status"].iloc[0] == "driver_cancelled"

    def test_not_accepted(self) -> None:
        df = _exp_df(accepted=False, completed=False)
        result, _ = engineer_experience_features(df)
        assert result["experience_status"].iloc[0] == "not_accepted"


# ---------------------------------------------------------------------------
# Preservation
# ---------------------------------------------------------------------------

class TestPreservation:
    def test_raw_columns_preserved(self) -> None:
        df = _exp_df()
        result, _ = engineer_experience_features(df)
        assert "completed" in result.columns
        assert "wait_time_minutes" in result.columns
        assert "surge_multiplier" in result.columns
        assert "cancelled_by_rider" in result.columns


# ---------------------------------------------------------------------------
# Feature columns
# ---------------------------------------------------------------------------

class TestFeatureColumns:
    def test_all_created(self) -> None:
        df = _exp_df()
        result, _ = engineer_experience_features(df)
        expected = [
            "wait_time_severity", "ride_completed", "ride_not_completed",
            "cancellation_type", "surge_exposure", "experience_status",
        ]
        for col in expected:
            assert col in result.columns


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

class TestReport:
    def test_report_created(self) -> None:
        df = _exp_df()
        _, report = engineer_experience_features(df)
        assert isinstance(report, ExperienceFeatureReport)
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
        result, report = engineer_experience_features(df)
        assert report.rows_processed == len(df)
        assert len(report.features_created) == 6
