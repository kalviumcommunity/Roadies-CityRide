"""Tests for missing value detection and imputation."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from roadies.quality.missing_values import (
    FIELD_POLICY,
    FieldMissingnessProfile,
    ImputationResult,
    ImputationStrategy,
    MissingValueProfile,
    MissingnessType,
    impute_missing_values,
    profile_missing_values,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_sample_df() -> pd.DataFrame:
    """Create a small sample DataFrame matching the schema."""
    return pd.DataFrame({
        "ride_id": [f"R-{i:06d}" for i in range(1, 11)],
        "rider_id": [f"RDR-{i:04d}" for i in range(1, 11)],
        "driver_id": [f"DRV-{i:04d}" if i % 3 != 0 else None for i in range(1, 11)],
        "request_timestamp": pd.date_range("2025-08-01T08:00:00", periods=10, freq="h"),
        "city": ["Mumbai", "Delhi", "Bangalore", "Mumbai", "Delhi",
                 "Chennai", "Pune", "Hyderabad", "Mumbai", "Delhi"],
        "accepted": [True, True, False, True, True, False, True, True, True, False],
        "completed": [True, True, False, True, False, False, True, True, True, False],
        "cancelled_by_rider": [False, False, False, False, True, False, False, False, False, True],
        "cancelled_by_driver": [False, False, False, False, False, False, False, False, False, False],
        "cancellation_reason": [None, None, None, None, "Changed mind", None, None, None, None, "Long wait time"],
        "driver_acceptance_rate": [0.85, 0.90, None, 0.78, 0.82, None, 0.88, 0.91, 0.80, None],
        "driver_rating": [4.5, 4.2, None, 4.0, 4.3, None, 4.6, 4.8, 4.1, None],
        "city_hour_requested_rides": [100, 80, 120, 95, 85, 70, 60, 55, 110, 90],
        "city_hour_available_drivers": [30, 25, 40, 28, 20, 18, 15, 12, 35, 22],
        "demand_level": ["high", "medium", "high", "medium", "high", "medium", "low", "low", "high", "medium"],
        "surge_multiplier": [1.5, 1.2, 1.8, 1.3, 1.6, 1.1, 1.0, 1.0, 1.7, 1.4],
        "base_fare": [120.0, 100.0, 130.0, 110.0, 125.0, 95.0, 85.0, 80.0, 135.0, 105.0],
        "wait_time_minutes": [5.0, 3.0, None, 7.0, 4.0, None, 2.0, 1.5, 6.0, None],
        "trip_duration_minutes": [20.0, 15.0, None, 25.0, None, None, 18.0, 12.0, 22.0, None],
        "trip_distance_km": [8.0, 5.0, None, 10.0, None, None, 7.0, 4.0, 9.0, None],
    })


# ---------------------------------------------------------------------------
# Detection of missing values
# ---------------------------------------------------------------------------

class TestMissingDetection:
    def test_detects_all_null_columns(self) -> None:
        df = _make_sample_df()
        profile = profile_missing_values(df)
        null_fields = {f.field_name for f in profile.fields_with_missing}
        # driver_id, cancellation_reason, driver_acceptance_rate, driver_rating,
        # wait_time_minutes, trip_duration_minutes, trip_distance_km
        assert "driver_id" in null_fields
        assert "cancellation_reason" in null_fields

    def test_total_missing_count(self) -> None:
        df = _make_sample_df()
        profile = profile_missing_values(df)
        assert profile.total_missing_before > 0

    def test_no_missing_columns_not_in_profile(self) -> None:
        df = _make_sample_df()
        profile = profile_missing_values(df)
        null_fields = {f.field_name for f in profile.fields_with_missing}
        assert "ride_id" not in null_fields
        assert "city" not in null_fields


# ---------------------------------------------------------------------------
# Expected nullable fields
# ---------------------------------------------------------------------------

class TestExpectedNullables:
    def test_driver_id_is_conditional(self) -> None:
        df = _make_sample_df()
        profile = profile_missing_values(df)
        driver = next(f for f in profile.fields_with_missing if f.field_name == "driver_id")
        assert driver.missingness_type == MissingnessType.CONDITIONAL_NULL

    def test_cancellation_reason_is_conditional(self) -> None:
        df = _make_sample_df()
        profile = profile_missing_values(df)
        cr = next(f for f in profile.fields_with_missing if f.field_name == "cancellation_reason")
        assert cr.missingness_type == MissingnessType.CONDITIONAL_NULL

    def test_wait_time_is_conditional(self) -> None:
        df = _make_sample_df()
        profile = profile_missing_values(df)
        wt = next(f for f in profile.fields_with_missing if f.field_name == "wait_time_minutes")
        assert wt.missingness_type == MissingnessType.CONDITIONAL_NULL


# ---------------------------------------------------------------------------
# Unexpected missing values
# ---------------------------------------------------------------------------

class TestUnexpectedMissing:
    def test_unexpected_field_flagged(self) -> None:
        df = _make_sample_df()
        # Add a column not in the policy with nulls
        df["custom_field"] = [1.0, None, 3.0, None, 5.0, None, 7.0, None, 9.0, None]
        profile = profile_missing_values(df)
        assert "custom_field" in profile.unexpected_missing

    def test_no_unexpected_when_clean(self) -> None:
        df = _make_sample_df()
        profile = profile_missing_values(df)
        assert len(profile.unexpected_missing) == 0


# ---------------------------------------------------------------------------
# Imputation strategies
# ---------------------------------------------------------------------------

class TestImputationStrategies:
    def test_keep_null_does_not_impute(self) -> None:
        df = _make_sample_df()
        result = impute_missing_values(df)
        for fp in result.profile.fields_with_missing:
            if fp.imputation_strategy == ImputationStrategy.KEEP_NULL:
                assert fp.values_imputed == 0

    def test_driver_id_remains_null(self) -> None:
        df = _make_sample_df()
        result = impute_missing_values(df)
        null_count = result.df["driver_id"].isnull().sum()
        assert null_count == df["driver_id"].isnull().sum()

    def test_cancellation_reason_remains_null(self) -> None:
        df = _make_sample_df()
        result = impute_missing_values(df)
        null_count = result.df["cancellation_reason"].isnull().sum()
        assert null_count == df["cancellation_reason"].isnull().sum()

    def test_custom_strategy_override(self) -> None:
        df = _make_sample_df()
        result = impute_missing_values(
            df,
            custom_strategies={"driver_acceptance_rate": ImputationStrategy.MEDIAN},
        )
        driver_rate = next(f for f in result.profile.fields_with_missing if f.field_name == "driver_acceptance_rate")
        assert driver_rate.values_imputed > 0
        assert result.df["driver_acceptance_rate"].isnull().sum() < df["driver_acceptance_rate"].isnull().sum()


# ---------------------------------------------------------------------------
# Preservation of expected nulls
# ---------------------------------------------------------------------------

class TestPreserveExpectedNulls:
    def test_all_expected_nulls_preserved_by_default(self) -> None:
        df = _make_sample_df()
        original_nulls = {
            col: df[col].isnull().sum()
            for col in FIELD_POLICY
            if col in df.columns
        }
        result = impute_missing_values(df)
        for col, expected_count in original_nulls.items():
            actual_count = result.df[col].isnull().sum()
            assert actual_count == expected_count, f"{col}: expected {expected_count} nulls, got {actual_count}"


# ---------------------------------------------------------------------------
# Imputation count tracking
# ---------------------------------------------------------------------------

class TestImputationTracking:
    def test_total_imputed_zero_by_default(self) -> None:
        df = _make_sample_df()
        result = impute_missing_values(df)
        assert result.profile.total_imputed == 0

    def test_values_imputed_tracked_per_field(self) -> None:
        df = _make_sample_df()
        result = impute_missing_values(
            df,
            custom_strategies={"driver_acceptance_rate": ImputationStrategy.MEDIAN},
        )
        driver_rate = next(f for f in result.profile.fields_with_missing if f.field_name == "driver_acceptance_rate")
        assert driver_rate.values_imputed == df["driver_acceptance_rate"].isnull().sum()


# ---------------------------------------------------------------------------
# Invalid imputation handling
# ---------------------------------------------------------------------------

class TestInvalidImputation:
    def test_no_imputation_on_empty_df(self) -> None:
        df = pd.DataFrame(columns=["ride_id", "city", "accepted"])
        result = impute_missing_values(df)
        assert result.profile.total_imputed == 0

    def test_original_df_not_modified(self) -> None:
        df = _make_sample_df()
        original_nulls = df.isnull().sum().sum()
        _ = impute_missing_values(df)
        assert df.isnull().sum().sum() == original_nulls


# ---------------------------------------------------------------------------
# Validation after imputation
# ---------------------------------------------------------------------------

class TestValidationAfterImputation:
    def test_imputation_result_has_validation_fields(self) -> None:
        df = _make_sample_df()
        result = impute_missing_values(df)
        assert isinstance(result, ImputationResult)
        assert result.validation_passed is True

    def test_changed_columns_listed(self) -> None:
        df = _make_sample_df()
        result = impute_missing_values(df)
        assert isinstance(result.changed_columns, list)


# ---------------------------------------------------------------------------
# Generated dataset integration
# ---------------------------------------------------------------------------

class TestGeneratedDatasetIntegration:
    def test_generated_dataset_profiles(self) -> None:
        """Profile the synthetic dataset from Issue #12."""
        csv_path = Path("/tmp/profile-test.csv")
        if not csv_path.exists():
            pytest.skip("Generated dataset not found")

        df = pd.read_csv(csv_path)
        profile = profile_missing_values(df)
        assert profile.total_rows == 100
        assert profile.total_missing_before > 0
        # All nulls should be expected
        assert len(profile.unexpected_missing) == 0

    def test_generated_dataset_imputation(self) -> None:
        """Impute the synthetic dataset — all expected nulls should be retained."""
        csv_path = Path("/tmp/profile-test.csv")
        if not csv_path.exists():
            pytest.skip("Generated dataset not found")

        df = pd.read_csv(csv_path)
        result = impute_missing_values(df)
        assert result.profile.total_imputed == 0
        assert result.profile.total_missing_after == result.profile.total_missing_before

    def test_validation_passes_after_imputation(self) -> None:
        """Post-imputation validation should pass."""
        csv_path = Path("/tmp/profile-test.csv")
        if not csv_path.exists():
            pytest.skip("Generated dataset not found")

        df = pd.read_csv(csv_path)
        result = impute_missing_values(df)
        assert result.validation_passed is True


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

class TestSummary:
    def test_summary_contains_key_info(self) -> None:
        df = _make_sample_df()
        profile = profile_missing_values(df)
        summary = profile.summary()
        assert "Missing Value Profile" in summary
        assert "Total missing before" in summary
        assert "driver_id" in summary
