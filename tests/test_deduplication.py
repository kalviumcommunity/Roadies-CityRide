"""Tests for duplicate detection and deduplication."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from roadies.quality.deduplication import (
    DeduplicationResult,
    DuplicateReport,
    deduplicate_dataset,
    detect_duplicates,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_sample_df() -> pd.DataFrame:
    """Create a clean sample DataFrame with no duplicates."""
    return pd.DataFrame({
        "ride_id": [f"R-{i:06d}" for i in range(1, 6)],
        "rider_id": [f"RDR-{i:04d}" for i in range(1, 6)],
        "driver_id": ["DRV-0001", "DRV-0002", None, "DRV-0004", None],
        "request_timestamp": pd.date_range("2025-08-01T08:00:00", periods=5, freq="h"),
        "city": ["Mumbai", "Delhi", "Bangalore", "Mumbai", "Delhi"],
        "accepted": [True, True, False, True, False],
        "completed": [True, False, False, True, False],
        "cancelled_by_rider": [False, True, False, False, True],
        "cancelled_by_driver": [False, False, False, False, False],
        "cancellation_reason": [None, "Changed mind", None, None, "Long wait time"],
        "driver_acceptance_rate": [0.85, 0.90, None, 0.78, None],
        "driver_rating": [4.5, 4.2, None, 4.0, None],
        "city_hour_requested_rides": [100, 80, 120, 95, 85],
        "city_hour_available_drivers": [30, 25, 40, 28, 20],
        "demand_level": ["high", "medium", "high", "medium", "high"],
        "surge_multiplier": [1.5, 1.2, 1.8, 1.3, 1.6],
        "base_fare": [120.0, 100.0, 130.0, 110.0, 125.0],
        "wait_time_minutes": [5.0, 3.0, None, 7.0, None],
        "trip_duration_minutes": [20.0, None, None, 25.0, None],
        "trip_distance_km": [8.0, None, None, 10.0, None],
    })


# ---------------------------------------------------------------------------
# No duplicates
# ---------------------------------------------------------------------------

class TestNoDuplicates:
    def test_clean_df_has_no_duplicates(self) -> None:
        df = _make_sample_df()
        report = detect_duplicates(df)
        assert report.exact_duplicate_count == 0
        assert report.duplicate_ride_id_count == 0
        assert report.conflicting_id_count == 0

    def test_deduplication_preserves_clean_df(self) -> None:
        df = _make_sample_df()
        result = deduplicate_dataset(df)
        assert result.report.rows_removed == 0
        assert result.report.final_row_count == 5


# ---------------------------------------------------------------------------
# Exact duplicate rows
# ---------------------------------------------------------------------------

class TestExactDuplicates:
    def test_exact_duplicates_detected(self) -> None:
        df = _make_sample_df()
        # Add an exact duplicate of row 0
        df = pd.concat([df, df.iloc[[0]]], ignore_index=True)
        report = detect_duplicates(df)
        assert report.exact_duplicate_count == 1

    def test_exact_duplicates_removed(self) -> None:
        df = _make_sample_df()
        df = pd.concat([df, df.iloc[[0]]], ignore_index=True)
        result = deduplicate_dataset(df)
        assert result.report.rows_removed == 1
        assert result.report.final_row_count == 5

    def test_multiple_exact_duplicates(self) -> None:
        df = _make_sample_df()
        df = pd.concat([df, df.iloc[[0]], df.iloc[[0]]], ignore_index=True)
        report = detect_duplicates(df)
        assert report.exact_duplicate_count == 2


# ---------------------------------------------------------------------------
# Duplicate ride IDs
# ---------------------------------------------------------------------------

class TestDuplicateRideIds:
    def test_duplicate_ids_detected(self) -> None:
        df = _make_sample_df()
        # Add a row with same ride_id but same values
        dup_row = df.iloc[[0]].copy()
        df = pd.concat([df, dup_row], ignore_index=True)
        report = detect_duplicates(df)
        assert report.duplicate_ride_id_count == 1
        assert "R-000001" in report.duplicate_ride_ids

    def test_duplicate_ids_removed(self) -> None:
        df = _make_sample_df()
        dup_row = df.iloc[[0]].copy()
        df = pd.concat([df, dup_row], ignore_index=True)
        result = deduplicate_dataset(df)
        assert result.report.final_row_count == 5


# ---------------------------------------------------------------------------
# Conflicting duplicate IDs
# ---------------------------------------------------------------------------

class TestConflictingDuplicates:
    def test_conflicting_ids_detected(self) -> None:
        df = _make_sample_df()
        # Add a row with same ride_id but different city
        dup_row = df.iloc[[0]].copy()
        dup_row["city"] = "Chennai"
        df = pd.concat([df, dup_row], ignore_index=True)
        report = detect_duplicates(df)
        assert report.conflicting_id_count == 1
        assert "R-000001" in report.conflicting_ids

    def test_conflicting_ids_not_silently_dropped(self) -> None:
        df = _make_sample_df()
        dup_row = df.iloc[[0]].copy()
        dup_row["city"] = "Chennai"
        df = pd.concat([df, dup_row], ignore_index=True)
        result = deduplicate_dataset(df)
        # First occurrence retained
        assert result.report.final_row_count == 5
        assert result.conflicts_df is not None
        assert len(result.conflicts_df) == 2


# ---------------------------------------------------------------------------
# Deterministic deduplication
# ---------------------------------------------------------------------------

class TestDeterministicDeduplication:
    def test_first_occurrence_retained(self) -> None:
        df = _make_sample_df()
        dup_row = df.iloc[[0]].copy()
        dup_row["city"] = "Chennai"
        df = pd.concat([df, dup_row], ignore_index=True)
        result = deduplicate_dataset(df)
        # First row should be the original Mumbai one
        assert result.df.iloc[0]["city"] == "Mumbai"


# ---------------------------------------------------------------------------
# Correct row counts
# ---------------------------------------------------------------------------

class TestRowCounts:
    def test_input_output_counts(self) -> None:
        df = _make_sample_df()
        df = pd.concat([df, df.iloc[[0]], df.iloc[[0]]], ignore_index=True)
        result = deduplicate_dataset(df)
        assert result.report.total_rows == 7
        assert result.report.rows_removed == 2
        assert result.report.final_row_count == 5


# ---------------------------------------------------------------------------
# Duplicate reporting
# ---------------------------------------------------------------------------

class TestDuplicateReporting:
    def test_report_has_summary(self) -> None:
        df = _make_sample_df()
        report = detect_duplicates(df)
        summary = report.summary()
        assert "Duplicate Report" in summary

    def test_result_has_report(self) -> None:
        df = _make_sample_df()
        result = deduplicate_dataset(df)
        assert isinstance(result.report, DuplicateReport)

    def test_conflicts_df_populated_when_conflicts(self) -> None:
        df = _make_sample_df()
        dup_row = df.iloc[[0]].copy()
        dup_row["city"] = "Chennai"
        df = pd.concat([df, dup_row], ignore_index=True)
        result = deduplicate_dataset(df)
        assert result.conflicts_df is not None


# ---------------------------------------------------------------------------
# Generated dataset integration
# ---------------------------------------------------------------------------

class TestGeneratedDatasetIntegration:
    def test_generated_dataset_has_no_duplicates(self) -> None:
        csv_path = Path("/tmp/profile-test.csv")
        if not csv_path.exists():
            pytest.skip("Generated dataset not found")

        df = pd.read_csv(csv_path)
        report = detect_duplicates(df)
        assert report.exact_duplicate_count == 0
        assert report.duplicate_ride_id_count == 0
        assert report.conflicting_id_count == 0

    def test_deduplication_preserves_generated_data(self) -> None:
        csv_path = Path("/tmp/profile-test.csv")
        if not csv_path.exists():
            pytest.skip("Generated dataset not found")

        df = pd.read_csv(csv_path)
        result = deduplicate_dataset(df)
        assert result.report.rows_removed == 0
        assert result.report.final_row_count == 100

    def test_post_deduplication_validation(self) -> None:
        from roadies.quality.validator import validate_dataset
        csv_path = Path("/tmp/profile-test.csv")
        if not csv_path.exists():
            pytest.skip("Generated dataset not found")

        df = pd.read_csv(csv_path)
        result = deduplicate_dataset(df)
        validation = validate_dataset(result.df)
        assert validation.passed
