"""Tests for funnel analysis and drop-off detection."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from roadies.analysis.funnel import (
    DropOffPoint,
    FunnelResult,
    FunnelStage,
    analyze_funnel,
    compare_funnels,
    compare_high_demand_funnel,
    get_drop_off_points,
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
        "is_high_demand": np.random.choice([True, False], n, p=[0.3, 0.7]),
    })


# ---------------------------------------------------------------------------
# Funnel counts
# ---------------------------------------------------------------------------

class TestFunnelCounts:
    def test_basic_funnel(self) -> None:
        df = _sample_df()
        results = analyze_funnel(df)
        assert len(results) == 1
        assert results[0].total_requested == 500

    def test_stage_counts(self) -> None:
        df = _sample_df()
        results = analyze_funnel(df)
        stages = {s.name: s.count for s in results[0].stages}
        assert stages["requested"] == 500
        assert stages["accepted"] > 0
        assert stages["completed"] > 0


# ---------------------------------------------------------------------------
# Conversion rates
# ---------------------------------------------------------------------------

class TestConversionRates:
    def test_conversion_rates(self) -> None:
        df = _sample_df()
        results = analyze_funnel(df)
        for stage in results[0].stages:
            assert 0 <= stage.rate <= 1.0


# ---------------------------------------------------------------------------
# Drop-off calculations
# ---------------------------------------------------------------------------

class TestDropOff:
    def test_drop_off_points(self) -> None:
        df = _sample_df()
        results = analyze_funnel(df)
        drop_offs = get_drop_off_points(results[0])
        assert len(drop_offs) == 2  # requested→accepted, accepted→completed
        for do in drop_offs:
            assert isinstance(do, DropOffPoint)
            assert do.count_lost >= 0
            assert 0 <= do.pct_lost <= 1.0


# ---------------------------------------------------------------------------
# Zero-stage handling
# ---------------------------------------------------------------------------

class TestZeroStage:
    def test_empty_df(self) -> None:
        df = pd.DataFrame()
        results = analyze_funnel(df)
        assert len(results) == 0


# ---------------------------------------------------------------------------
# City grouping
# ---------------------------------------------------------------------------

class TestCityGrouping:
    def test_city_funnel(self) -> None:
        df = _sample_df()
        results = analyze_funnel(df, group_by=["city"])
        assert len(results) == 3
        for r in results:
            assert "city" in r.group

    def test_comparison(self) -> None:
        df = _sample_df()
        comp = compare_funnels(df, group_by=["city"])
        assert len(comp) == 3
        assert "city" in comp.columns


# ---------------------------------------------------------------------------
# High-demand comparison
# ---------------------------------------------------------------------------

class TestHighDemand:
    def test_comparison(self) -> None:
        df = _sample_df()
        comp = compare_high_demand_funnel(df)
        assert len(comp) == 3  # normal, high, change
        assert "demand_period" in comp.columns

    def test_change_row(self) -> None:
        df = _sample_df()
        comp = compare_high_demand_funnel(df)
        change = comp[comp["demand_period"] == "change"]
        assert len(change) == 1


# ---------------------------------------------------------------------------
# Deterministic results
# ---------------------------------------------------------------------------

class TestDeterministic:
    def test_same_input_same_output(self) -> None:
        df = _sample_df()
        r1 = analyze_funnel(df)
        r2 = analyze_funnel(df)
        assert r1[0].total_requested == r2[0].total_requested
        for s1, s2 in zip(r1[0].stages, r2[0].stages):
            assert s1.count == s2.count
