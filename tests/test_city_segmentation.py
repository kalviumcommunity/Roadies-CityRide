"""Tests for city segmentation and comparison analysis."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from roadies.analysis.city_segmentation import (
    CityComparison,
    CityProfile,
    CityRanking,
    CitySegmentationReport,
    compute_city_summary,
    compare_normal_vs_high_demand,
    rank_cities,
    segment_cities,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sample_df() -> pd.DataFrame:
    np.random.seed(42)
    n = 200
    cities = np.random.choice(["Mumbai", "Delhi", "Bangalore"], n)
    return pd.DataFrame({
        "ride_id": [f"R-{i:06d}" for i in range(n)],
        "city": cities,
        "was_accepted": np.random.choice([True, False], n, p=[0.8, 0.2]),
        "rider_cancelled": np.random.choice([True, False], n, p=[0.1, 0.9]),
        "driver_cancelled": np.random.choice([True, False], n, p=[0.03, 0.97]),
        "ride_completed": np.random.choice([True, False], n, p=[0.7, 0.3]),
        "wait_time_minutes": np.random.uniform(2, 30, n),
        "surge_multiplier": np.random.uniform(1, 3, n),
        "demand_supply_ratio": np.random.uniform(1, 10, n),
        "is_high_demand": np.random.choice([True, False], n),
    })


# ---------------------------------------------------------------------------
# City summary
# ---------------------------------------------------------------------------

class TestCitySummary:
    def test_computes_summary(self) -> None:
        df = _sample_df()
        summary = compute_city_summary(df)
        assert len(summary) == 3
        assert "city" in summary.columns
        assert "ride_volume" in summary.columns

    def test_all_cities_present(self) -> None:
        df = _sample_df()
        summary = compute_city_summary(df)
        assert set(summary["city"]) == {"Mumbai", "Delhi", "Bangalore"}


# ---------------------------------------------------------------------------
# High-demand comparison
# ---------------------------------------------------------------------------

class TestHighDemandComparison:
    def test_comparison(self) -> None:
        df = _sample_df()
        results = compare_normal_vs_high_demand(df)
        assert len(results) > 0

    def test_returns_city_comparison(self) -> None:
        df = _sample_df()
        results = compare_normal_vs_high_demand(df)
        assert all(isinstance(r, CityComparison) for r in results)


# ---------------------------------------------------------------------------
# Rankings
# ---------------------------------------------------------------------------

class TestRankings:
    def test_rankings(self) -> None:
        df = _sample_df()
        rankings = rank_cities(df)
        assert len(rankings) > 0

    def test_rankings_ordered(self) -> None:
        df = _sample_df()
        rankings = rank_cities(df)
        for ranking in rankings:
            values = [v for _, v in ranking.rankings]
            # Check ordered (ascending for cancel/surge/wait)
            if ranking.metric in ("rider_cancel_rate", "avg_wait", "avg_surge"):
                assert values == sorted(values)
            else:
                assert values == sorted(values, reverse=True)


# ---------------------------------------------------------------------------
# Segmentation
# ---------------------------------------------------------------------------

class TestSegmentation:
    def test_segmentation(self) -> None:
        df = _sample_df()
        report = segment_cities(df)
        assert isinstance(report, CitySegmentationReport)
        assert len(report.city_profiles) == 3
        assert all(isinstance(p, CityProfile) for p in report.city_profiles)

    def test_segments_assigned(self) -> None:
        df = _sample_df()
        report = segment_cities(df)
        valid_segments = {"stable", "demand-constrained", "surge-sensitive", "cancellation-sensitive", "high-pressure"}
        for p in report.city_profiles:
            assert p.segment in valid_segments


# ---------------------------------------------------------------------------
# Missing/empty
# ---------------------------------------------------------------------------

class TestMissing:
    def test_empty_city(self) -> None:
        df = pd.DataFrame({
            "ride_id": ["R-001"],
            "city": ["Mumbai"],
            "was_accepted": [True],
            "rider_cancelled": [False],
            "surge_multiplier": [1.0],
            "wait_time_minutes": [5.0],
        })
        summary = compute_city_summary(df)
        assert len(summary) == 1
