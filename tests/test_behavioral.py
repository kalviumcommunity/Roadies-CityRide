"""Tests for behavioural analysis and user segmentation."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from roadies.analysis.behavioral import (
    MIN_DRIVER_RIDES,
    MIN_RIDER_RIDES,
    SegmentSummary,
    analyze_driver_behaviour,
    analyze_repeated_behaviour,
    analyze_rider_behaviour,
    compare_behaviour_by_demand,
    segment_drivers,
    segment_riders,
    summarize_driver_segments,
    summarize_rider_segments,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sample_df() -> pd.DataFrame:
    np.random.seed(42)
    n = 500
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
        "is_high_demand": np.random.choice([True, False], n, p=[0.3, 0.7]),
    })


# ---------------------------------------------------------------------------
# Rider analysis
# ---------------------------------------------------------------------------

class TestRiderAnalysis:
    def test_rider_behaviour(self) -> None:
        df = _sample_df()
        result = analyze_rider_behaviour(df)
        assert len(result) > 0
        assert "cancellation_rate" in result.columns

    def test_rider_segmentation(self) -> None:
        df = _sample_df()
        result = segment_riders(df)
        assert "cancellation_sensitive" in result.columns
        assert "completion_oriented" in result.columns

    def test_rider_summaries(self) -> None:
        df = _sample_df()
        summaries = summarize_rider_segments(df)
        assert len(summaries) > 0
        for s in summaries:
            assert isinstance(s, SegmentSummary)
            assert s.segment_type == "rider"


# ---------------------------------------------------------------------------
# Driver analysis
# ---------------------------------------------------------------------------

class TestDriverAnalysis:
    def test_driver_behaviour(self) -> None:
        df = _sample_df()
        result = analyze_driver_behaviour(df)
        assert len(result) > 0
        assert "acceptance_rate" in result.columns

    def test_driver_segmentation(self) -> None:
        df = _sample_df()
        result = segment_drivers(df)
        assert "high_acceptance" in result.columns
        assert "cancellation_prone" in result.columns

    def test_driver_summaries(self) -> None:
        df = _sample_df()
        summaries = summarize_driver_segments(df)
        assert len(summaries) > 0
        for s in summaries:
            assert isinstance(s, SegmentSummary)
            assert s.segment_type == "driver"


# ---------------------------------------------------------------------------
# Threshold logic
# ---------------------------------------------------------------------------

class TestThresholds:
    def test_cancellation_sensitive(self) -> None:
        df = _sample_df()
        riders = segment_riders(df)
        sensitive = riders[riders["cancellation_sensitive"] == True]
        assert all(sensitive["cancellation_rate"] > 0.30)

    def test_high_acceptance(self) -> None:
        df = _sample_df()
        drivers = segment_drivers(df)
        high = drivers[drivers["high_acceptance"] == True]
        assert all(high["acceptance_rate"] > 0.90)


# ---------------------------------------------------------------------------
# Overlapping segments
# ---------------------------------------------------------------------------

class TestOverlapping:
    def test_rider_multiple_segments(self) -> None:
        df = _sample_df()
        riders = segment_riders(df)
        # Some riders may belong to multiple segments
        multi = riders[
            (riders["cancellation_sensitive"] == True) &
            (riders["high_wait_exposure"] == True)
        ]
        # May or may not exist, but should not error
        assert isinstance(multi, pd.DataFrame)


# ---------------------------------------------------------------------------
# High-demand comparison
# ---------------------------------------------------------------------------

class TestHighDemand:
    def test_comparison(self) -> None:
        df = _sample_df()
        result = compare_behaviour_by_demand(df)
        assert "high" in result
        assert "normal" in result
        assert "change_pct" in result


# ---------------------------------------------------------------------------
# Repeated behaviour
# ---------------------------------------------------------------------------

class TestRepeated:
    def test_repeated_behaviour(self) -> None:
        df = _sample_df()
        result = analyze_repeated_behaviour(df)
        assert "riders" in result
        assert "drivers" in result


# ---------------------------------------------------------------------------
# Missing user IDs
# ---------------------------------------------------------------------------

class TestMissingIDs:
    def test_missing_rider_id(self) -> None:
        df = _sample_df()
        df = df.drop(columns=["rider_id"])
        result = analyze_rider_behaviour(df)
        assert len(result) == 0

    def test_missing_driver_id(self) -> None:
        df = _sample_df()
        df = df.drop(columns=["driver_id"])
        result = analyze_driver_behaviour(df)
        assert len(result) == 0


# ---------------------------------------------------------------------------
# Minimum observations
# ---------------------------------------------------------------------------

class TestMinObservations:
    def test_large_min_rides(self) -> None:
        df = _sample_df()
        riders = segment_riders(df, min_rides=1000)
        assert len(riders) == 0


# ---------------------------------------------------------------------------
# Deterministic results
# ---------------------------------------------------------------------------

class TestDeterministic:
    def test_same_input_same_output(self) -> None:
        df = _sample_df()
        r1 = segment_riders(df)
        r2 = segment_riders(df)
        pd.testing.assert_frame_equal(r1, r2)
