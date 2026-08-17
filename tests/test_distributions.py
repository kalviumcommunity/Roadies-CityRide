"""Tests for distribution analysis functions."""

from __future__ import annotations

import pandas as pd
import pytest

from roadies.analysis.distributions import (
    CityComparison,
    CategoricalStats,
    HighDemandComparison,
    NumericalStats,
    compute_categorical_stats,
    compute_numerical_stats,
    compare_cities,
    compare_high_demand,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sample_df() -> pd.DataFrame:
    return pd.DataFrame({
        "city": ["Mumbai", "Delhi", "Mumbai", "Delhi", "Mumbai"],
        "surge_multiplier": [1.0, 1.5, 2.0, 1.0, 1.3],
        "wait_time_minutes": [5.0, 10.0, 3.0, 8.0, 12.0],
        "is_high_demand": [False, True, True, False, True],
    })


# ---------------------------------------------------------------------------
# Numerical stats
# ---------------------------------------------------------------------------

class TestNumericalStats:
    def test_basic_stats(self) -> None:
        df = _sample_df()
        stats = compute_numerical_stats(df, ["surge_multiplier"])
        assert len(stats) == 1
        assert stats[0].column == "surge_multiplier"
        assert stats[0].count == 5
        assert stats[0].mean == pytest.approx(1.36)

    def test_multiple_columns(self) -> None:
        df = _sample_df()
        stats = compute_numerical_stats(df, ["surge_multiplier", "wait_time_minutes"])
        assert len(stats) == 2

    def test_nonexistent_column_skipped(self) -> None:
        df = _sample_df()
        stats = compute_numerical_stats(df, ["nonexistent"])
        assert len(stats) == 0


# ---------------------------------------------------------------------------
# Categorical stats
# ---------------------------------------------------------------------------

class TestCategoricalStats:
    def test_basic_stats(self) -> None:
        df = _sample_df()
        stats = compute_categorical_stats(df, ["city"])
        assert len(stats) == 1
        assert stats[0].column == "city"
        assert stats[0].categories["Mumbai"] == 3
        assert stats[0].categories["Delhi"] == 2


# ---------------------------------------------------------------------------
# High-demand comparison
# ---------------------------------------------------------------------------

class TestHighDemandComparison:
    def test_comparison(self) -> None:
        df = _sample_df()
        results = compare_high_demand(df, ["surge_multiplier"])
        assert len(results) == 1
        assert results[0].metric == "surge_multiplier"
        assert results[0].high_mean > 0

    def test_no_high_demand_column(self) -> None:
        df = pd.DataFrame({"surge_multiplier": [1.0, 2.0]})
        results = compare_high_demand(df)
        assert len(results) == 0


# ---------------------------------------------------------------------------
# City comparison
# ---------------------------------------------------------------------------

class TestCityComparison:
    def test_comparison(self) -> None:
        df = _sample_df()
        results = compare_cities(df, ["surge_multiplier"])
        assert len(results) == 2  # Mumbai and Delhi
        cities = [r.city for r in results]
        assert "Mumbai" in cities
        assert "Delhi" in cities

    def test_no_city_column(self) -> None:
        df = pd.DataFrame({"surge_multiplier": [1.0, 2.0]})
        results = compare_cities(df)
        assert len(results) == 0
