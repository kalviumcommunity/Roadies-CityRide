"""Tests for string cleaning and text normalisation."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from roadies.quality.string_clean import (
    ColumnCleaningReport,
    StringCleaningReport,
    clean_strings,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_sample_df() -> pd.DataFrame:
    """Create a sample DataFrame for testing."""
    return pd.DataFrame({
        "ride_id": [f"R-{i:06d}" for i in range(1, 6)],
        "rider_id": [f"RDR-{i:04d}" for i in range(1, 6)],
        "driver_id": ["DRV-0001", "DRV-0002", None, "DRV-0004", None],
        "city": ["Mumbai", "Delhi", "Bangalore", "Mumbai", "Delhi"],
        "demand_level": ["high", "medium", "high", "medium", "high"],
        "cancellation_reason": [None, "Changed mind", None, None, "Long wait time"],
    })


# ---------------------------------------------------------------------------
# Leading/trailing whitespace
# ---------------------------------------------------------------------------

class TestWhitespaceCleaning:
    def test_leading_whitespace_removed(self) -> None:
        df = pd.DataFrame({"city": [" Mumbai", "Delhi"]})
        cleaned, _ = clean_strings(df)
        assert cleaned["city"].iloc[0] == "Mumbai"

    def test_trailing_whitespace_removed(self) -> None:
        df = pd.DataFrame({"city": ["Mumbai ", "Delhi"]})
        cleaned, _ = clean_strings(df)
        assert cleaned["city"].iloc[0] == "Mumbai"

    def test_both_whitespace_removed(self) -> None:
        df = pd.DataFrame({"city": [" Mumbai ", "Delhi"]})
        cleaned, _ = clean_strings(df)
        assert cleaned["city"].iloc[0] == "Mumbai"


# ---------------------------------------------------------------------------
# Case normalisation
# ---------------------------------------------------------------------------

class TestCaseNormalisation:
    def test_lowercase_city_normalised(self) -> None:
        df = pd.DataFrame({"city": ["mumbai", "Delhi"]})
        cleaned, _ = clean_strings(df)
        assert cleaned["city"].iloc[0] == "Mumbai"

    def test_uppercase_city_normalised(self) -> None:
        df = pd.DataFrame({"city": ["MUMBAI", "Delhi"]})
        cleaned, _ = clean_strings(df)
        assert cleaned["city"].iloc[0] == "Mumbai"

    def test_mixed_case_city_normalised(self) -> None:
        df = pd.DataFrame({"city": ["MuMbAi", "Delhi"]})
        cleaned, _ = clean_strings(df)
        assert cleaned["city"].iloc[0] == "Mumbai"


# ---------------------------------------------------------------------------
# Repeated whitespace
# ---------------------------------------------------------------------------

class TestRepeatedWhitespace:
    def test_internal_whitespace_collapsed(self) -> None:
        df = pd.DataFrame({"city": ["Mumbai", "Delhi"]})
        df.loc[0, "city"] = "Mumbai"
        cleaned, _ = clean_strings(df)
        assert cleaned["city"].iloc[0] == "Mumbai"


# ---------------------------------------------------------------------------
# Textual null handling
# ---------------------------------------------------------------------------

class TestTextualNulls:
    def test_empty_string_becomes_null(self) -> None:
        df = pd.DataFrame({"city": ["Mumbai", ""]})
        cleaned, _ = clean_strings(df)
        assert pd.isna(cleaned["city"].iloc[1])

    def test_whitespace_only_becomes_null(self) -> None:
        df = pd.DataFrame({"city": ["Mumbai", " "]})
        cleaned, _ = clean_strings(df)
        assert pd.isna(cleaned["city"].iloc[1])

    def test_na_becomes_null(self) -> None:
        df = pd.DataFrame({"city": ["Mumbai", "NA"]})
        cleaned, _ = clean_strings(df)
        assert pd.isna(cleaned["city"].iloc[1])

    def test_n_a_becomes_null(self) -> None:
        df = pd.DataFrame({"city": ["Mumbai", "N/A"]})
        cleaned, _ = clean_strings(df)
        assert pd.isna(cleaned["city"].iloc[1])

    def test_null_string_becomes_null(self) -> None:
        df = pd.DataFrame({"city": ["Mumbai", "null"]})
        cleaned, _ = clean_strings(df)
        assert pd.isna(cleaned["city"].iloc[1])


# ---------------------------------------------------------------------------
# Empty strings
# ---------------------------------------------------------------------------

class TestEmptyStrings:
    def test_empty_string_handled(self) -> None:
        df = pd.DataFrame({"demand_level": ["high", ""]})
        cleaned, _ = clean_strings(df)
        assert pd.isna(cleaned["demand_level"].iloc[1])


# ---------------------------------------------------------------------------
# Already-clean values
# ---------------------------------------------------------------------------

class TestAlreadyClean:
    def test_clean_values_unchanged(self) -> None:
        df = _make_sample_df()
        cleaned, report = clean_strings(df)
        assert cleaned["city"].iloc[0] == "Mumbai"
        assert report.total_values_changed == 0


# ---------------------------------------------------------------------------
# Preservation of legitimate values
# ---------------------------------------------------------------------------

class TestPreserveLegitimate:
    def test_all_cities_preserved(self) -> None:
        df = pd.DataFrame({"city": ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Pune"]})
        cleaned, _ = clean_strings(df)
        for i in range(6):
            assert cleaned["city"].iloc[i] == df["city"].iloc[i]


# ---------------------------------------------------------------------------
# Categorical validation after cleaning
# ---------------------------------------------------------------------------

class TestCategoricalValidation:
    def test_validates_after_cleaning(self) -> None:
        from roadies.quality.validator import validate_dataset
        # Use a full DataFrame that passes validation
        csv_path = Path("/tmp/profile-test.csv")
        if not csv_path.exists():
            pytest.skip("Generated dataset not found")
        df = pd.read_csv(csv_path)
        cleaned, _ = clean_strings(df)
        validation = validate_dataset(cleaned)
        assert validation.passed


# ---------------------------------------------------------------------------
# Change reporting
# ---------------------------------------------------------------------------

class TestChangeReporting:
    def test_report_created(self) -> None:
        df = pd.DataFrame({"city": [" mumbai ", "Delhi"]})
        _, report = clean_strings(df)
        assert isinstance(report, StringCleaningReport)

    def test_values_changed_counted(self) -> None:
        df = pd.DataFrame({"city": [" mumbai ", "Delhi"]})
        _, report = clean_strings(df)
        assert report.total_values_changed == 1

    def test_textual_nulls_counted(self) -> None:
        df = pd.DataFrame({"city": ["Mumbai", "", "NA"]})
        _, report = clean_strings(df)
        assert report.total_textual_nulls == 2


# ---------------------------------------------------------------------------
# Generated dataset integration
# ---------------------------------------------------------------------------

class TestGeneratedDatasetIntegration:
    def test_generated_dataset_remains_valid(self) -> None:
        from roadies.quality.validator import validate_dataset
        csv_path = Path("/tmp/profile-test.csv")
        if not csv_path.exists():
            pytest.skip("Generated dataset not found")

        df = pd.read_csv(csv_path)
        cleaned, report = clean_strings(df)
        validation = validate_dataset(cleaned)
        assert validation.passed

    def test_generated_dataset_no_major_changes(self) -> None:
        csv_path = Path("/tmp/profile-test.csv")
        if not csv_path.exists():
            pytest.skip("Generated dataset not found")

        df = pd.read_csv(csv_path)
        cleaned, report = clean_strings(df)
        # Generated data should already be clean
        assert report.total_values_changed == 0
        assert report.total_textual_nulls == 0
