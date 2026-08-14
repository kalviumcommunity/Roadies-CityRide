"""Tests for statistical outlier detection."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from roadies.quality.outlier import (
    FieldOutlierReport,
    OutlierDetectionReport,
    detect_outliers,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _outlier_df(col: str, values: list[float]) -> pd.DataFrame:
    return pd.DataFrame({col: values})


# ---------------------------------------------------------------------------
# IQR detection
# ---------------------------------------------------------------------------

class TestIQR:
    def test_known_outlier(self) -> None:
        df = _outlier_df("surge_multiplier", [1.0, 1.0, 1.0, 1.0, 1.0, 10.0])
        report = detect_outliers(df)
        field = next(f for f in report.fields_analysed if f.column == "surge_multiplier")
        assert field.method == "IQR"
        assert field.outlier_count >= 1

    def test_no_outliers(self) -> None:
        df = _outlier_df("surge_multiplier", [1.0, 1.2, 1.1, 1.0, 1.3])
        report = detect_outliers(df)
        field = next(f for f in report.fields_analysed if f.column == "surge_multiplier")
        assert field.outlier_count == 0


# ---------------------------------------------------------------------------
# Z-score detection
# ---------------------------------------------------------------------------

class TestZScore:
    def test_known_outlier(self) -> None:
        vals = [100, 105, 95, 110, 102, 98, 108, 103, 97, 101, 5000]
        df = _outlier_df("base_fare", vals)
        report = detect_outliers(df)
        field = next(f for f in report.fields_analysed if f.column == "base_fare")
        assert field.method == "z-score"
        assert field.outlier_count >= 1

    def test_no_outliers(self) -> None:
        df = _outlier_df("base_fare", [100, 105, 95, 110, 102])
        report = detect_outliers(df)
        field = next(f for f in report.fields_analysed if f.column == "base_fare")
        assert field.outlier_count == 0


# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

class TestThresholds:
    def test_lower_threshold(self) -> None:
        df = _outlier_df("wait_time_minutes", [5, 5, 5, 5, 5, 100])
        report = detect_outliers(df)
        field = next(f for f in report.fields_analysed if f.column == "wait_time_minutes")
        assert field.lower_threshold is not None
        assert field.upper_threshold is not None


# ---------------------------------------------------------------------------
# Outlier counts and percentages
# ---------------------------------------------------------------------------

class TestCounts:
    def test_percentage_calculation(self) -> None:
        df = _outlier_df("surge_multiplier", [1.0, 1.0, 1.0, 1.0, 1.0, 10.0])
        report = detect_outliers(df)
        field = next(f for f in report.fields_analysed if f.column == "surge_multiplier")
        assert 0 <= field.outlier_pct <= 100


# ---------------------------------------------------------------------------
# Summary statistics
# ---------------------------------------------------------------------------

class TestSummaryStats:
    def test_min_max_median(self) -> None:
        df = _outlier_df("surge_multiplier", [1.0, 2.0, 3.0, 4.0, 5.0])
        report = detect_outliers(df)
        field = next(f for f in report.fields_analysed if f.column == "surge_multiplier")
        assert field.min_val == 1.0
        assert field.max_val == 5.0
        assert field.median_val == 3.0


# ---------------------------------------------------------------------------
# Non-numeric columns excluded
# ---------------------------------------------------------------------------

class TestExclusions:
    def test_non_numeric_skipped(self) -> None:
        df = pd.DataFrame({"city": ["Mumbai", "Delhi"], "surge_multiplier": [1.0, 5.0]})
        report = detect_outliers(df)
        assert not any(f.column == "city" for f in report.fields_analysed)


# ---------------------------------------------------------------------------
# Affected indices
# ---------------------------------------------------------------------------

class TestAffectedIndices:
    def test_indices_recorded(self) -> None:
        df = _outlier_df("surge_multiplier", [1.0, 1.0, 1.0, 1.0, 1.0, 10.0])
        report = detect_outliers(df)
        field = next(f for f in report.fields_analysed if f.column == "surge_multiplier")
        if field.outlier_count > 0:
            assert len(field.affected_indices) == field.outlier_count


# ---------------------------------------------------------------------------
# Generated dataset integration
# ---------------------------------------------------------------------------

class TestGeneratedDatasetIntegration:
    def test_generated_dataset(self) -> None:
        csv_path = Path("/tmp/profile-test.csv")
        if not csv_path.exists():
            pytest.skip("Generated dataset not found")
        df = pd.read_csv(csv_path)
        report = detect_outliers(df)
        assert report.total_rows == len(df)
        assert len(report.fields_analysed) > 0
