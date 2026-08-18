"""Tests for GroupBy aggregation and segment insights."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from roadies.analysis.groupby_segments import (
    MIN_SEGMENT_SIZE,
    SegmentInsight,
    SegmentRanking,
    aggregate_by_segment,
    compare_segments,
    rank_segments,
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
        "demand_period": np.random.choice(["low", "normal", "high"], n),
        "surge_category": np.random.choice(["none", "low", "moderate", "high"], n),
        "was_accepted": np.random.choice([True, False], n, p=[0.8, 0.2]),
        "ride_completed": np.random.choice([True, False], n, p=[0.7, 0.3]),
        "rider_cancelled": np.random.choice([True, False], n, p=[0.1, 0.9]),
        "wait_time_minutes": np.random.uniform(2, 30, n),
        "surge_multiplier": np.random.uniform(1, 3, n),
    })


# ---------------------------------------------------------------------------
# Single-column grouping
# ---------------------------------------------------------------------------

class TestSingleGrouping:
    def test_single_column(self) -> None:
        df = _sample_df()
        result = aggregate_by_segment(df, ["city"])
        assert len(result) == 3
        assert "segment_size" in result.columns

    def test_all_cities_present(self) -> None:
        df = _sample_df()
        result = aggregate_by_segment(df, ["city"])
        assert set(result["city"]) == {"Mumbai", "Delhi", "Bangalore"}


# ---------------------------------------------------------------------------
# Multi-column grouping
# ---------------------------------------------------------------------------

class TestMultiGrouping:
    def test_multi_column(self) -> None:
        df = _sample_df()
        result = aggregate_by_segment(df, ["city", "demand_period"])
        assert len(result) > 3  # Multiple combinations

    def test_has_all_groups(self) -> None:
        df = _sample_df()
        result = aggregate_by_segment(df, ["city", "demand_period"])
        assert "city" in result.columns
        assert "demand_period" in result.columns


# ---------------------------------------------------------------------------
# Metric aggregation
# ---------------------------------------------------------------------------

class TestMetrics:
    def test_metrics_calculated(self) -> None:
        df = _sample_df()
        result = aggregate_by_segment(df, ["city"])
        assert "was_accepted_mean" in result.columns or "was_accepted" in result.columns

    def test_segment_size(self) -> None:
        df = _sample_df()
        result = aggregate_by_segment(df, ["city"])
        assert result["segment_size"].sum() == len(df)


# ---------------------------------------------------------------------------
# Compare segments
# ---------------------------------------------------------------------------

class TestCompare:
    def test_compare(self) -> None:
        df = _sample_df()
        agg, insights = compare_segments(df, ["city"])
        assert len(agg) > 0
        assert isinstance(insights, list)

    def test_insights_structure(self) -> None:
        df = _sample_df()
        _, insights = compare_segments(df, ["city"])
        for i in insights:
            assert isinstance(i, SegmentInsight)
            assert i.description
            assert i.metric


# ---------------------------------------------------------------------------
# Rankings
# ---------------------------------------------------------------------------

class TestRankings:
    def test_ranking(self) -> None:
        df = _sample_df()
        ranking = rank_segments(df, ["city"], "rider_cancelled")
        assert isinstance(ranking, SegmentRanking)
        assert len(ranking.rankings) > 0

    def test_ranking_ordered(self) -> None:
        df = _sample_df()
        ranking = rank_segments(df, ["city"], "rider_cancelled", ascending=True)
        values = [v for _, v in ranking.rankings]
        assert values == sorted(values)


# ---------------------------------------------------------------------------
# Empty data
# ---------------------------------------------------------------------------

class TestEmpty:
    def test_empty_df(self) -> None:
        df = pd.DataFrame()
        result = aggregate_by_segment(df, ["city"])
        assert len(result) == 0


# ---------------------------------------------------------------------------
# Missing grouping columns
# ---------------------------------------------------------------------------

class TestMissingColumns:
    def test_missing_column_skipped(self) -> None:
        df = _sample_df()
        result = aggregate_by_segment(df, ["nonexistent"])
        assert len(result) == 0


# ---------------------------------------------------------------------------
# Minimum segment size
# ---------------------------------------------------------------------------

class TestMinSize:
    def test_large_min_size(self) -> None:
        df = _sample_df()
        agg, insights = compare_segments(df, ["city"], min_size=10000)
        # No segments large enough
        assert len(insights) == 0


# ---------------------------------------------------------------------------
# Nullable fields
# ---------------------------------------------------------------------------

class TestNullable:
    def test_nullable_metric(self) -> None:
        df = _sample_df()
        df.loc[0, "wait_time_minutes"] = None
        result = aggregate_by_segment(df, ["city"])
        assert len(result) == 3
