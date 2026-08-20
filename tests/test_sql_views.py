"""Tests for SQL query optimization and aggregation views."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from roadies.database import (
    create_database,
    create_views,
    execute_metric_query,
    get_view_list,
    load_dataframe,
    query,
    query_view,
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
    create_views(db_path)
    return db_path


# ---------------------------------------------------------------------------
# View existence
# ---------------------------------------------------------------------------

class TestViewExistence:
    def test_views_created(self, temp_db: Path) -> None:
        views = get_view_list(temp_db)
        assert "vw_city_performance" in views
        assert "vw_city_demand_comparison" in views
        assert "vw_city_deterioration" in views
        assert "vw_rider_experience" in views


# ---------------------------------------------------------------------------
# View schema
# ---------------------------------------------------------------------------

class TestViewSchema:
    def test_city_performance_columns(self, temp_db: Path) -> None:
        result = query_view("vw_city_performance", temp_db)
        assert "city" in result.columns
        assert "acceptance_rate" in result.columns
        assert "rider_cancel_rate" in result.columns


# ---------------------------------------------------------------------------
# Aggregation grain
# ---------------------------------------------------------------------------

class TestAggregationGrain:
    def test_city_performance_grain(self, temp_db: Path) -> None:
        result = query_view("vw_city_performance", temp_db)
        assert len(result) == 3  # 3 cities

    def test_city_demand_comparison_grain(self, temp_db: Path) -> None:
        result = query_view("vw_city_demand_comparison", temp_db)
        assert len(result) == 6  # 3 cities × 2 demand periods


# ---------------------------------------------------------------------------
# Metric correctness
# ---------------------------------------------------------------------------

class TestMetricCorrectness:
    def test_city_performance_metrics(self, temp_db: Path) -> None:
        result = query_view("vw_city_performance", temp_db)
        # Check that metrics are within valid ranges
        assert all(0 <= result["acceptance_rate"]) <= 100
        assert all(0 <= result["rider_cancel_rate"]) <= 100

    def test_city_deterioration_metrics(self, temp_db: Path) -> None:
        result = query_view("vw_city_deterioration", temp_db)
        assert "acceptance_change" in result.columns
        assert "cancel_change" in result.columns


# ---------------------------------------------------------------------------
# Result equivalence
# ---------------------------------------------------------------------------

class TestResultEquivalence:
    def test_city_performance_matches_direct(self, temp_db: Path) -> None:
        # View result should match direct query
        view_result = query_view("vw_city_performance", temp_db)
        direct_result = execute_metric_query("city_metrics", temp_db)

        # Sort both by city for comparison
        view_sorted = view_result.sort_values("city").reset_index(drop=True)
        direct_sorted = direct_result.sort_values("city").reset_index(drop=True)

        pd.testing.assert_frame_equal(view_sorted, direct_sorted)


# ---------------------------------------------------------------------------
# Query execution
# ---------------------------------------------------------------------------

class TestQueryExecution:
    def test_query_view_with_limit(self, temp_db: Path) -> None:
        result = query_view("vw_city_performance", temp_db, limit=2)
        assert len(result) == 2


# ---------------------------------------------------------------------------
# Aggregation tables
# ---------------------------------------------------------------------------

class TestAggregationTables:
    def test_daily_metrics_table(self, temp_db: Path) -> None:
        result = query("SELECT * FROM agg_daily_metrics", temp_db)
        assert len(result) > 0
        assert "updated_at" in result.columns

    def test_city_metrics_table(self, temp_db: Path) -> None:
        result = query("SELECT * FROM agg_city_metrics", temp_db)
        assert len(result) == 3


# ---------------------------------------------------------------------------
# Generated database integration
# ---------------------------------------------------------------------------

class TestIntegration:
    def test_all_views_queryable(self, temp_db: Path) -> None:
        views = ["vw_city_performance", "vw_city_demand_comparison",
                 "vw_city_deterioration", "vw_rider_experience"]
        for v in views:
            result = query_view(v, temp_db)
            assert len(result) > 0
