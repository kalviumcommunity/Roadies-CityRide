"""Tests for root-cause investigation of degraded cities."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from roadies.analysis.root_cause import (
    CityComparison,
    DegradedCity,
    OperationalLink,
    assess_city_consistency,
    compare_degraded_vs_stable,
    identify_degraded_cities,
    trace_operational_chain,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sample_df() -> pd.DataFrame:
    np.random.seed(42)
    n = 500
    return pd.DataFrame({
        "ride_id": [f"R-{i:06d}" for i in range(n)],
        "city": np.random.choice(["Mumbai", "Delhi", "Bangalore"], n),
        "was_accepted": np.random.choice([True, False], n, p=[0.8, 0.2]),
        "ride_completed": np.random.choice([True, False], n, p=[0.7, 0.3]),
        "rider_cancelled": np.random.choice([True, False], n, p=[0.1, 0.9]),
        "driver_cancelled": np.random.choice([True, False], n, p=[0.05, 0.95]),
        "wait_time_minutes": np.random.uniform(2, 30, n),
        "surge_multiplier": np.random.uniform(1, 3, n),
        "demand_supply_ratio": np.random.uniform(0.5, 2.0, n),
        "is_high_demand": np.random.choice([True, False], n, p=[0.3, 0.7]),
    })


# ---------------------------------------------------------------------------
# Degraded-city identification
# ---------------------------------------------------------------------------

class TestDegradedCities:
    def test_identification(self) -> None:
        df = _sample_df()
        result = identify_degraded_cities(df)
        assert isinstance(result, list)

    def test_degraded_city_structure(self) -> None:
        df = _sample_df()
        result = identify_degraded_cities(df)
        for city in result:
            assert isinstance(city, DegradedCity)
            assert city.city
            assert 0 <= city.deterioration_score <= 1.0


# ---------------------------------------------------------------------------
# Comparison calculations
# ---------------------------------------------------------------------------

class TestComparison:
    def test_comparison(self) -> None:
        df = _sample_df()
        degraded = ["Mumbai"]
        result = compare_degraded_vs_stable(df, degraded)
        assert len(result) == 2  # degraded and stable
        categories = {c.category for c in result}
        assert "degraded" in categories
        assert "stable" in categories


# ---------------------------------------------------------------------------
# Absolute/relative change
# ---------------------------------------------------------------------------

class TestChange:
    def test_deterioration_values(self) -> None:
        df = _sample_df()
        degraded = ["Mumbai"]
        result = compare_degraded_vs_stable(df, degraded)
        for comp in result:
            assert isinstance(comp.deterioration, dict)


# ---------------------------------------------------------------------------
# City consistency
# ---------------------------------------------------------------------------

class TestConsistency:
    def test_consistency(self) -> None:
        df = _sample_df()
        result = assess_city_consistency(df)
        assert isinstance(result, dict)
        assert "Mumbai" in result


# ---------------------------------------------------------------------------
# Operational chain
# ---------------------------------------------------------------------------

class TestOperationalChain:
    def test_chain(self) -> None:
        df = _sample_df()
        links = trace_operational_chain(df)
        assert isinstance(links, list)
        for link in links:
            assert isinstance(link, OperationalLink)
            assert link.from_factor
            assert link.to_factor


# ---------------------------------------------------------------------------
# Insufficient sample sizes
# ---------------------------------------------------------------------------

class TestInsufficient:
    def test_empty_df(self) -> None:
        df = pd.DataFrame()
        result = identify_degraded_cities(df)
        assert len(result) == 0


# ---------------------------------------------------------------------------
# Deterministic outputs
# ---------------------------------------------------------------------------

class TestDeterministic:
    def test_same_input_same_output(self) -> None:
        df = _sample_df()
        r1 = identify_degraded_cities(df)
        r2 = identify_degraded_cities(df)
        assert len(r1) == len(r2)
        for c1, c2 in zip(r1, r2):
            assert c1.city == c2.city
