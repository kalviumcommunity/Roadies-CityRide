"""Tests for SQL business metrics queries."""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from roadies.database import (
    create_database,
    execute_metric_query,
    get_connection,
    load_dataframe,
    query,
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
# Core metric correctness
# ---------------------------------------------------------------------------

class TestCoreMetrics:
    def test_core_metrics(self, temp_db: Path) -> None:
        result = execute_metric_query("core_metrics", temp_db)
        assert len(result) == 1
        assert result["total_rides"].iloc[0] == 200
        assert 0 <= result["acceptance_rate"].iloc[0] <= 100

    def test_manual_validation(self, temp_db: Path) -> None:
        # Manual calculation
        df = query("SELECT * FROM rides", temp_db)
        expected_acceptance = df["was_accepted"].mean() * 100

        result = execute_metric_query("core_metrics", temp_db)
        actual_acceptance = result["acceptance_rate"].iloc[0]
        assert abs(actual_acceptance - expected_acceptance) < 0.1


# ---------------------------------------------------------------------------
# City aggregation
# ---------------------------------------------------------------------------

class TestCityMetrics:
    def test_city_metrics(self, temp_db: Path) -> None:
        result = execute_metric_query("city_metrics", temp_db)
        assert len(result) == 3  # Mumbai, Delhi, Bangalore
        assert "city" in result.columns
        assert "acceptance_rate" in result.columns

    def test_city_volume_sum(self, temp_db: Path) -> None:
        result = execute_metric_query("city_metrics", temp_db)
        total = result["ride_volume"].sum()
        assert total == 200


# ---------------------------------------------------------------------------
# Normal vs high-demand comparison
# ---------------------------------------------------------------------------

class TestDemandComparison:
    def test_demand_comparison(self, temp_db: Path) -> None:
        result = execute_metric_query("demand_comparison", temp_db)
        assert len(result) == 2  # normal, high
        assert "demand_period" in result.columns

    def test_demand_periods(self, temp_db: Path) -> None:
        result = execute_metric_query("demand_comparison", temp_db)
        periods = set(result["demand_period"])
        assert "normal" in periods
        assert "high" in periods


# ---------------------------------------------------------------------------
# Time aggregation
# ---------------------------------------------------------------------------

class TestTimeMetrics:
    def test_daily_metrics(self, temp_db: Path) -> None:
        result = execute_metric_query("daily_metrics", temp_db)
        assert len(result) > 0
        assert "ride_date" in result.columns

    def test_hourly_metrics(self, temp_db: Path) -> None:
        result = execute_metric_query("hourly_metrics", temp_db)
        assert len(result) > 0
        assert "ride_hour" in result.columns


# ---------------------------------------------------------------------------
# City deterioration
# ---------------------------------------------------------------------------

class TestCityDeterioration:
    def test_deterioration(self, temp_db: Path) -> None:
        result = execute_metric_query("city_deterioration", temp_db)
        assert len(result) == 3
        assert "acceptance_change" in result.columns
        assert "cancel_change" in result.columns


# ---------------------------------------------------------------------------
# Empty dataset behaviour
# ---------------------------------------------------------------------------

class TestEmptyDataset:
    def test_empty_core_metrics(self, tmp_path: Path) -> None:
        db_path = tmp_path / "empty.db"
        create_database(db_path)
        result = execute_metric_query("core_metrics", db_path)
        assert result["total_rides"].iloc[0] == 0


# ---------------------------------------------------------------------------
# Query execution
# ---------------------------------------------------------------------------

class TestQueryExecution:
    def test_unknown_query(self, temp_db: Path) -> None:
        with pytest.raises(ValueError, match="Unknown query"):
            execute_metric_query("nonexistent", temp_db)


# ---------------------------------------------------------------------------
# Generated database integration
# ---------------------------------------------------------------------------

class TestIntegration:
    def test_all_queries(self, temp_db: Path) -> None:
        queries = ["core_metrics", "city_metrics", "demand_comparison",
                    "daily_metrics", "hourly_metrics", "city_deterioration"]
        for q in queries:
            result = execute_metric_query(q, temp_db)
            assert len(result) > 0
