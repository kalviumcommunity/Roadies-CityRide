"""Tests for data-type standardisation."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from roadies.quality.standardize import (
    ColumnConversion,
    StandardizationResult,
    standardize_dtypes,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_sample_df() -> pd.DataFrame:
    """Create a sample DataFrame with mixed types (simulating CSV ingestion)."""
    return pd.DataFrame({
        "ride_id": [f"R-{i:06d}" for i in range(1, 6)],
        "rider_id": [f"RDR-{i:04d}" for i in range(1, 6)],
        "driver_id": ["DRV-0001", "DRV-0002", None, "DRV-0004", None],
        "request_timestamp": [
            "2025-08-01T08:00:00", "2025-08-01T09:00:00",
            "2025-08-01T10:00:00", "2025-08-01T11:00:00",
            "2025-08-01T12:00:00",
        ],
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
# Integer/numeric conversion
# ---------------------------------------------------------------------------

class TestNumericConversion:
    def test_integer_columns_stay_int(self) -> None:
        df = _make_sample_df()
        result = standardize_dtypes(df)
        assert result.df["city_hour_requested_rides"].dtype in ("int64", "int32", "int")

    def test_float_columns_stay_float(self) -> None:
        df = _make_sample_df()
        result = standardize_dtypes(df)
        assert pd.api.types.is_float_dtype(result.df["surge_multiplier"])

    def test_nullable_float_preserves_nulls(self) -> None:
        df = _make_sample_df()
        result = standardize_dtypes(df)
        null_count = result.df["driver_acceptance_rate"].isnull().sum()
        assert null_count == df["driver_acceptance_rate"].isnull().sum()

    def test_string_numeric_converted(self) -> None:
        df = pd.DataFrame({"city_hour_requested_rides": ["100", "200", "300"]})
        result = standardize_dtypes(df)
        assert result.df["city_hour_requested_rides"].iloc[0] == 100


# ---------------------------------------------------------------------------
# Boolean conversion
# ---------------------------------------------------------------------------

class TestBooleanConversion:
    def test_bool_columns_are_boolean(self) -> None:
        df = _make_sample_df()
        result = standardize_dtypes(df)
        assert result.df["accepted"].dtype == "boolean" or result.df["accepted"].dtype == bool

    def test_string_true_false_converted(self) -> None:
        df = pd.DataFrame({"accepted": ["true", "false", "true"]})
        result = standardize_dtypes(df)
        # Should be boolean type
        assert result.df["accepted"].dtype == "boolean" or result.df["accepted"].dtype == bool

    def test_numeric_0_1_converted(self) -> None:
        df = pd.DataFrame({"accepted": [1, 0, 1]})
        result = standardize_dtypes(df)
        assert result.df["accepted"].iloc[0] is True or result.df["accepted"].iloc[0] == True


# ---------------------------------------------------------------------------
# Categorical standardisation
# ---------------------------------------------------------------------------

class TestCategoricalStandardization:
    def test_city_stays_string(self) -> None:
        df = _make_sample_df()
        result = standardize_dtypes(df)
        assert result.df["city"].dtype == object or pd.api.types.is_string_dtype(result.df["city"])

    def test_demand_level_stays_string(self) -> None:
        df = _make_sample_df()
        result = standardize_dtypes(df)
        assert result.df["demand_level"].dtype == object or pd.api.types.is_string_dtype(result.df["demand_level"])


# ---------------------------------------------------------------------------
# Datetime conversion
# ---------------------------------------------------------------------------

class TestDatetimeConversion:
    def test_timestamp_converted_to_datetime(self) -> None:
        df = _make_sample_df()
        result = standardize_dtypes(df)
        assert pd.api.types.is_datetime64_any_dtype(result.df["request_timestamp"])

    def test_datetime_values_preserved(self) -> None:
        df = _make_sample_df()
        result = standardize_dtypes(df)
        assert result.df["request_timestamp"].iloc[0] == pd.Timestamp("2025-08-01 08:00:00")


# ---------------------------------------------------------------------------
# Nullable fields
# ---------------------------------------------------------------------------

class TestNullableFields:
    def test_driver_id_nulls_preserved(self) -> None:
        df = _make_sample_df()
        result = standardize_dtypes(df)
        assert result.df["driver_id"].isnull().sum() == df["driver_id"].isnull().sum()

    def test_cancellation_reason_nulls_preserved(self) -> None:
        df = _make_sample_df()
        result = standardize_dtypes(df)
        assert result.df["cancellation_reason"].isnull().sum() == 3

    def test_wait_time_nulls_preserved(self) -> None:
        df = _make_sample_df()
        result = standardize_dtypes(df)
        assert result.df["wait_time_minutes"].isnull().sum() == 2


# ---------------------------------------------------------------------------
# Already-correct data
# ---------------------------------------------------------------------------

class TestAlreadyCorrect:
    def test_already_correct_types_no_change(self) -> None:
        df = _make_sample_df()
        result1 = standardize_dtypes(df)
        result2 = standardize_dtypes(result1.df)
        # Second pass should have 0 conversions
        assert result2.total_converted == 0


# ---------------------------------------------------------------------------
# Invalid values
# ---------------------------------------------------------------------------

class TestInvalidValues:
    def test_non_numeric_string_reported(self) -> None:
        df = pd.DataFrame({"city_hour_requested_rides": [100, "abc", 300]})
        result = standardize_dtypes(df)
        assert result.total_failures > 0 or result.conversions[0].conversion_failures > 0

    def test_invalid_datetime_reported(self) -> None:
        df = pd.DataFrame({"request_timestamp": ["2025-08-01", "not-a-date"]})
        result = standardize_dtypes(df)
        conv = next(c for c in result.conversions if c.column == "request_timestamp")
        assert conv.conversion_failures > 0


# ---------------------------------------------------------------------------
# Conversion reporting
# ---------------------------------------------------------------------------

class TestConversionReporting:
    def test_result_has_conversions(self) -> None:
        df = _make_sample_df()
        result = standardize_dtypes(df)
        assert len(result.conversions) > 0

    def test_result_has_summary(self) -> None:
        df = _make_sample_df()
        result = standardize_dtypes(df)
        summary = result.summary()
        assert "Standardization result" in summary

    def test_unexpected_columns_flagged(self) -> None:
        df = _make_sample_df()
        df["extra_col"] = [1, 2, 3, 4, 5]
        result = standardize_dtypes(df)
        assert "extra_col" in result.unexpected_columns


# ---------------------------------------------------------------------------
# Validator compatibility
# ---------------------------------------------------------------------------

class TestValidatorCompatibility:
    def test_validates_after_standardization(self) -> None:
        from roadies.quality.validator import validate_dataset
        df = _make_sample_df()
        result = standardize_dtypes(df)
        validation = validate_dataset(result.df)
        assert validation.passed


# ---------------------------------------------------------------------------
# Generated dataset integration
# ---------------------------------------------------------------------------

class TestGeneratedDatasetIntegration:
    def test_generated_dataset_standardizes(self) -> None:
        csv_path = Path("/tmp/profile-test.csv")
        if not csv_path.exists():
            pytest.skip("Generated dataset not found")

        df = pd.read_csv(csv_path)
        result = standardize_dtypes(df)
        assert result.total_failures == 0
        assert pd.api.types.is_datetime64_any_dtype(result.df["request_timestamp"])

    def test_validation_passes_after_standardization(self) -> None:
        from roadies.quality.validator import validate_dataset
        csv_path = Path("/tmp/profile-test.csv")
        if not csv_path.exists():
            pytest.skip("Generated dataset not found")

        df = pd.read_csv(csv_path)
        result = standardize_dtypes(df)
        validation = validate_dataset(result.df)
        assert validation.passed

    def test_nulls_preserved_in_generated_data(self) -> None:
        csv_path = Path("/tmp/profile-test.csv")
        if not csv_path.exists():
            pytest.skip("Generated dataset not found")

        df = pd.read_csv(csv_path)
        original_nulls = df["driver_id"].isnull().sum()
        result = standardize_dtypes(df)
        assert result.df["driver_id"].isnull().sum() == original_nulls
