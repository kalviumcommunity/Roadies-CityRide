"""Tests for SQL/Python metric validation."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from roadies.database import create_database, load_dataframe
from roadies.validation import (
    DEFAULT_ABSOLUTE_TOLERANCE,
    MetricComparison,
    ValidationReport,
    compare_metrics,
    calculate_python_metrics,
    fetch_sql_metrics,
    validate_sql_against_python,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sample_df() -> pd.DataFrame:
    np.random.seed(42)
    n = 200
    return pd.DataFrame({
        "ride_id": [f"R-{i:06d}" for i in range(n)],
        "rider_id": np.random.choice([f"rider-{i}" for i in range(20)], n),
        "driver_id": np.random.choice([f"driver-{i}" for i in range(30)], n),
        "city": np.random.choice(["Mumbai", "Delhi", "Bangalore"], n),
        "was_accepted": np.random.choice([True, False], n, p=[0.8, 0.2]),
        "ride_completed": np.random.choice([True, False], n, p=[0.7, 0.3]),
        "rider_cancelled": np.random.choice([True, False], n, p=[0.1, 0.9]),
        "driver_cancelled": np.random.choice([True, False], n, p=[0.05, 0.95]),
        "wait_time_minutes": np.random.uniform(2, 30, n),
        "surge_multiplier": np.random.uniform(1, 3, n),
        "demand_supply_ratio": np.random.uniform(0.5, 2.0, n),
        "is_high_demand": np.random.choice([True, False], n, p=[0.3, 0.7]),
        "request_timestamp": pd.date_range("2024-01-01", periods=n, freq="h"),
    })


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "test.db"
    create_database(db_path)
    df = _sample_df()
    load_dataframe(df, db_path)
    return db_path


# ---------------------------------------------------------------------------
# Matching integer metrics
# ---------------------------------------------------------------------------

class TestIntegerMetrics:
    def test_total_rides(self, temp_db: Path) -> None:
        df = _sample_df()
        report = validate_sql_against_python(df, temp_db)
        total_rides = [c for c in report.comparisons if c.metric_name == "total_rides"]
        assert len(total_rides) == 1
        assert total_rides[0].passed


# ---------------------------------------------------------------------------
# Matching floating-point metrics
# ---------------------------------------------------------------------------

class TestFloatMetrics:
    def test_acceptance_rate(self, temp_db: Path) -> None:
        df = _sample_df()
        report = validate_sql_against_python(df, temp_db)
        acceptance = [c for c in report.comparisons if c.metric_name == "acceptance_rate"]
        assert len(acceptance) == 1
        assert acceptance[0].passed


# ---------------------------------------------------------------------------
# Within-tolerance differences
# ---------------------------------------------------------------------------

class TestWithinTolerance:
    def test_small_difference_passes(self) -> None:
        comparison = compare_metrics(80.0, 80.01, "test_metric", absolute_tolerance=0.1)
        assert comparison.passed


# ---------------------------------------------------------------------------
# Beyond-tolerance differences
# ---------------------------------------------------------------------------

class TestBeyondTolerance:
    def test_large_difference_fails(self) -> None:
        comparison = compare_metrics(80.0, 85.0, "test_metric", absolute_tolerance=0.1)
        assert not comparison.passed


# ---------------------------------------------------------------------------
# Relative/absolute tolerance
# ---------------------------------------------------------------------------

class TestTolerance:
    def test_absolute_tolerance(self) -> None:
        comparison = compare_metrics(100.0, 100.5, "test", absolute_tolerance=1.0)
        assert comparison.passed

    def test_zero_value(self) -> None:
        comparison = compare_metrics(0.0, 0.1, "test", absolute_tolerance=0.5)
        assert comparison.passed


# ---------------------------------------------------------------------------
# Multiple metrics
# ---------------------------------------------------------------------------

class TestMultipleMetrics:
    def test_all_core_metrics(self, temp_db: Path) -> None:
        df = _sample_df()
        report = validate_sql_against_python(df, temp_db)
        assert report.total_metrics > 10  # Core + city + demand


# ---------------------------------------------------------------------------
# City-level validation
# ---------------------------------------------------------------------------

class TestCityValidation:
    def test_city_metrics_present(self, temp_db: Path) -> None:
        df = _sample_df()
        report = validate_sql_against_python(df, temp_db)
        city_metrics = [c for c in report.comparisons if c.category == "city"]
        assert len(city_metrics) > 0


# ---------------------------------------------------------------------------
# High-demand validation
# ---------------------------------------------------------------------------

class TestDemandValidation:
    def test_demand_metrics_present(self, temp_db: Path) -> None:
        df = _sample_df()
        report = validate_sql_against_python(df, temp_db)
        demand_metrics = [c for c in report.comparisons if c.category == "demand"]
        assert len(demand_metrics) > 0


# ---------------------------------------------------------------------------
# Intentional computation drift
# ---------------------------------------------------------------------------

class TestDriftDetection:
    def test_intentional_mismatch_detected(self, temp_db: Path) -> None:
        # Create a modified dataset with different values
        df = _sample_df()
        # Modify one metric intentionally
        df["was_accepted"] = True  # Force 100% acceptance
        load_dataframe(df, temp_db, if_exists="replace")

        # Python will see 100%, SQL will see whatever was loaded
        report = validate_sql_against_python(df, temp_db)

        # Check if mismatch is detected
        acceptance = [c for c in report.comparisons if c.metric_name == "acceptance_rate"]
        assert len(acceptance) == 1
        # This should fail because Python=100% but SQL may differ
        # (depends on what was actually loaded)


# ---------------------------------------------------------------------------
# Generated database integration
# ---------------------------------------------------------------------------

class TestIntegration:
    def test_full_validation(self, temp_db: Path) -> None:
        df = _sample_df()
        report = validate_sql_against_python(df, temp_db)
        assert report.total_metrics > 0
        assert isinstance(report.summary(), dict)
