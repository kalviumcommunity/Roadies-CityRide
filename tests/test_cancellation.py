"""Tests for rider cancellation behaviour feature engineering."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from roadies.features.cancellation import (
    CancellationFeatureReport,
    engineer_cancellation_features,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cancel_df(
    rider_cancel: bool = False,
    driver_cancel: bool = False,
    accepted: bool = True,
    reason: str | None = None,
) -> pd.DataFrame:
    return pd.DataFrame({
        "ride_id": ["R-001"],
        "cancelled_by_rider": [rider_cancel],
        "cancelled_by_driver": [driver_cancel],
        "accepted": [accepted],
        "cancellation_reason": [reason],
    })


# ---------------------------------------------------------------------------
# Cancelled ride
# ---------------------------------------------------------------------------

class TestCancelled:
    def test_rider_cancelled(self) -> None:
        df = _cancel_df(rider_cancel=True, reason="Changed mind")
        result, _ = engineer_cancellation_features(df)
        assert result["rider_cancelled"].iloc[0] == True
        assert result["any_cancelled"].iloc[0] == True

    def test_driver_cancelled(self) -> None:
        df = _cancel_df(driver_cancel=True, reason="Other")
        result, _ = engineer_cancellation_features(df)
        assert result["driver_cancelled"].iloc[0] == True
        assert result["any_cancelled"].iloc[0] == True


# ---------------------------------------------------------------------------
# Non-cancelled ride
# ---------------------------------------------------------------------------

class TestNotCancelled:
    def test_no_cancellation(self) -> None:
        df = _cancel_df()
        result, _ = engineer_cancellation_features(df)
        assert result["rider_cancelled"].iloc[0] == False
        assert result["driver_cancelled"].iloc[0] == False
        assert result["any_cancelled"].iloc[0] == False


# ---------------------------------------------------------------------------
# Cancellation reason handling
# ---------------------------------------------------------------------------

class TestReason:
    def test_wait_related(self) -> None:
        df = _cancel_df(rider_cancel=True, reason="Long wait time")
        result, _ = engineer_cancellation_features(df)
        assert result["cancellation_reason_category"].iloc[0] == "wait_related"

    def test_driver_behaviour(self) -> None:
        df = _cancel_df(rider_cancel=True, reason="Driver rude")
        result, _ = engineer_cancellation_features(df)
        assert result["cancellation_reason_category"].iloc[0] == "driver_behaviour"

    def test_rider_decision(self) -> None:
        df = _cancel_df(rider_cancel=True, reason="Changed mind")
        result, _ = engineer_cancellation_features(df)
        assert result["cancellation_reason_category"].iloc[0] == "rider_decision"

    def test_vehicle_related(self) -> None:
        df = _cancel_df(rider_cancel=True, reason="Vehicle quality")
        result, _ = engineer_cancellation_features(df)
        assert result["cancellation_reason_category"].iloc[0] == "vehicle_related"

    def test_other_reason(self) -> None:
        df = _cancel_df(rider_cancel=True, reason="Other")
        result, _ = engineer_cancellation_features(df)
        assert result["cancellation_reason_category"].iloc[0] == "other"


# ---------------------------------------------------------------------------
# Nullable cancellation reason
# ---------------------------------------------------------------------------

class TestNullable:
    def test_null_reason_not_cancelled(self) -> None:
        df = _cancel_df()
        result, _ = engineer_cancellation_features(df)
        assert result["has_cancellation_reason"].iloc[0] == False
        assert result["cancellation_reason_category"].iloc[0] == "unknown"


# ---------------------------------------------------------------------------
# Lifecycle edge cases
# ---------------------------------------------------------------------------

class TestLifecycle:
    def test_cancelled_before_acceptance(self) -> None:
        df = _cancel_df(rider_cancel=True, accepted=False)
        result, _ = engineer_cancellation_features(df)
        assert result["cancelled_before_acceptance"].iloc[0] == True
        assert result["cancelled_after_acceptance"].iloc[0] == False

    def test_cancelled_after_acceptance(self) -> None:
        df = _cancel_df(rider_cancel=True, accepted=True)
        result, _ = engineer_cancellation_features(df)
        assert result["cancelled_before_acceptance"].iloc[0] == False
        assert result["cancelled_after_acceptance"].iloc[0] == True


# ---------------------------------------------------------------------------
# Preservation
# ---------------------------------------------------------------------------

class TestPreservation:
    def test_raw_columns_preserved(self) -> None:
        df = _cancel_df(rider_cancel=True, reason="Changed mind")
        result, _ = engineer_cancellation_features(df)
        assert "cancelled_by_rider" in result.columns
        assert "cancelled_by_driver" in result.columns
        assert "cancellation_reason" in result.columns
        assert "accepted" in result.columns


# ---------------------------------------------------------------------------
# Feature columns
# ---------------------------------------------------------------------------

class TestFeatureColumns:
    def test_all_created(self) -> None:
        df = _cancel_df()
        result, _ = engineer_cancellation_features(df)
        expected = [
            "rider_cancelled", "driver_cancelled", "any_cancelled",
            "has_cancellation_reason", "cancellation_reason_category",
            "cancelled_before_acceptance", "cancelled_after_acceptance",
        ]
        for col in expected:
            assert col in result.columns


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

class TestReport:
    def test_report_created(self) -> None:
        df = _cancel_df()
        _, report = engineer_cancellation_features(df)
        assert isinstance(report, CancellationFeatureReport)
        assert len(report.features_created) == 7


# ---------------------------------------------------------------------------
# Generated dataset integration
# ---------------------------------------------------------------------------

class TestGeneratedDataset:
    def test_generated_dataset(self) -> None:
        csv_path = Path("/tmp/profile-test.csv")
        if not csv_path.exists():
            pytest.skip("Generated dataset not found")
        df = pd.read_csv(csv_path)
        result, report = engineer_cancellation_features(df)
        assert report.rows_processed == len(df)
        assert len(report.features_created) == 7
