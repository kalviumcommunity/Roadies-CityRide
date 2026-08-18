"""Tests for correlation and relationship analysis."""

from __future__ import annotations

import pandas as pd
import pytest

from roadies.analysis.relationships import (
    CorrelationResult,
    RelationshipReport,
    compare_relationships_by_city,
    compare_relationships_by_demand,
    compute_correlations,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sample_df() -> pd.DataFrame:
    import numpy as np
    np.random.seed(42)
    n = 100
    return pd.DataFrame({
        "demand_supply_ratio": np.random.uniform(1, 10, n),
        "surge_multiplier": np.random.uniform(1, 3, n),
        "wait_time_minutes": np.random.uniform(2, 30, n),
        "driver_acceptance_rate": np.random.uniform(0.5, 1.0, n),
        "rider_cancelled": np.random.choice([True, False], n),
        "ride_completed": np.random.choice([True, False], n),
        "city": np.random.choice(["Mumbai", "Delhi"], n),
        "is_high_demand": np.random.choice([True, False], n),
    })


# ---------------------------------------------------------------------------
# Correlation calculation
# ---------------------------------------------------------------------------

class TestCorrelation:
    def test_computes_correlations(self) -> None:
        df = _sample_df()
        results = compute_correlations(df)
        assert len(results) > 0

    def test_returns_correlation_result(self) -> None:
        df = _sample_df()
        results = compute_correlations(df)
        assert all(isinstance(r, CorrelationResult) for r in results)

    def test_coefficient_range(self) -> None:
        df = _sample_df()
        results = compute_correlations(df)
        for r in results:
            assert -1.0 <= r.coefficient <= 1.0


# ---------------------------------------------------------------------------
# High-demand comparison
# ---------------------------------------------------------------------------

class TestHighDemandComparison:
    def test_comparison(self) -> None:
        df = _sample_df()
        high, normal = compare_relationships_by_demand(df)
        assert len(high) > 0
        assert len(normal) > 0

    def test_no_high_demand_column(self) -> None:
        df = pd.DataFrame({"demand_supply_ratio": [1, 2], "surge_multiplier": [1, 2]})
        high, normal = compare_relationships_by_demand(df)
        assert len(high) == 0
        assert len(normal) == 0


# ---------------------------------------------------------------------------
# City-level comparison
# ---------------------------------------------------------------------------

class TestCityComparison:
    def test_comparison(self) -> None:
        df = _sample_df()
        results = compare_relationships_by_city(df, "demand_supply_ratio", "surge_multiplier")
        assert len(results) == 2  # Mumbai and Delhi

    def test_no_city_column(self) -> None:
        df = pd.DataFrame({"demand_supply_ratio": [1, 2], "surge_multiplier": [1, 2]})
        results = compare_relationships_by_city(df, "demand_supply_ratio", "surge_multiplier")
        assert len(results) == 0


# ---------------------------------------------------------------------------
# Missing values
# ---------------------------------------------------------------------------

class TestMissing:
    def test_handles_missing(self) -> None:
        df = _sample_df()
        df.loc[0, "demand_supply_ratio"] = None
        results = compute_correlations(df)
        assert len(results) > 0


# ---------------------------------------------------------------------------
# Insufficient sample
# ---------------------------------------------------------------------------

class TestInsufficient:
    def test_small_dataset(self) -> None:
        df = pd.DataFrame({
            "demand_supply_ratio": [1, 2],
            "surge_multiplier": [1, 2],
        })
        results = compute_correlations(df)
        # May return empty due to insufficient samples for some pairs
        assert isinstance(results, list)
