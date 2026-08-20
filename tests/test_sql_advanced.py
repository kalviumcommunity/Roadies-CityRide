"""Tests for SQL advanced analysis with joins and window functions."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from roadies.database import (
    create_database,
    execute_advanced_query,
    execute_metric_query,
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
# Join correctness
# ---------------------------------------------------------------------------

class TestJoins:
    def test_city_baseline_join(self, temp_db: Path) -> None:
        result = execute_advanced_query("within_city_baseline", temp_db)
        assert len(result) == 3  # 3 cities
        assert "city" in result.columns
        assert "normal_wait" in result.columns
        assert "high_wait" in result.columns


# ---------------------------------------------------------------------------
# Row-count preservation
# ---------------------------------------------------------------------------

class TestRowCount:
    def test_contribution_sum(self, temp_db: Path) -> None:
        result = execute_advanced_query("city_contribution", temp_db)
        total_rides = result["city_rides"].sum()
        assert total_rides == 200


# ---------------------------------------------------------------------------
# Ranking results
# ---------------------------------------------------------------------------

class TestRanking:
    def test_cancel_ranking(self, temp_db: Path) -> None:
        result = execute_advanced_query("city_cancel_ranking", temp_db)
        assert "cancel_rank" in result.columns
        ranks = result["cancel_rank"].tolist()
        assert ranks == sorted(ranks)  # Should be ordered

    def test_deterioration_ranking(self, temp_db: Path) -> None:
        result = execute_advanced_query("city_deterioration_ranking", temp_db)
        assert "deterioration_rank" in result.columns


# ---------------------------------------------------------------------------
# Partitioning by city
# ---------------------------------------------------------------------------

class TestPartitioning:
    def test_within_city_baseline(self, temp_db: Path) -> None:
        result = execute_advanced_query("within_city_baseline", temp_db)
        assert len(result) == 3
        # All cities should have both normal and high values
        assert result["normal_wait"].notna().all()
        assert result["high_wait"].notna().all()


# ---------------------------------------------------------------------------
# Ordering behaviour
# ---------------------------------------------------------------------------

class TestOrdering:
    def test_deviation_ordering(self, temp_db: Path) -> None:
        result = execute_advanced_query("city_deviation", temp_db)
        cancel_vs_avg = result["cancel_vs_avg"].tolist()
        assert cancel_vs_avg == sorted(cancel_vs_avg, reverse=True)


# ---------------------------------------------------------------------------
# High-demand comparison
# ---------------------------------------------------------------------------

class TestHighDemand:
    def test_high_demand_in_ranking(self, temp_db: Path) -> None:
        result = execute_advanced_query("city_cancel_ranking", temp_db)
        # Should only include high-demand data
        assert len(result) > 0


# ---------------------------------------------------------------------------
# Window calculations
# ---------------------------------------------------------------------------

class TestWindowCalculations:
    def test_running_metrics(self, temp_db: Path) -> None:
        result = execute_advanced_query("running_metrics", temp_db)
        assert "running_total" in result.columns
        assert "moving_avg_7day" in result.columns
        # Running total should increase
        running = result["running_total"].values
        assert all(running[i] <= running[i+1] for i in range(len(running)-1))


# ---------------------------------------------------------------------------
# Empty/edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_unknown_query(self, temp_db: Path) -> None:
        with pytest.raises(ValueError, match="Unknown advanced query"):
            execute_advanced_query("nonexistent", temp_db)


# ---------------------------------------------------------------------------
# Generated database integration
# ---------------------------------------------------------------------------

class TestIntegration:
    def test_all_advanced_queries(self, temp_db: Path) -> None:
        queries = [
            "city_cancel_ranking",
            "city_deterioration_ranking",
            "within_city_baseline",
            "running_metrics",
            "city_contribution",
            "city_deviation",
        ]
        for q in queries:
            result = execute_advanced_query(q, temp_db)
            assert len(result) > 0
