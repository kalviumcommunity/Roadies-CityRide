"""Tests for time-series trend and rolling metrics analysis."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from roadies.analysis.time_series import (
    aggregate_time_series,
    analyze_city_time_series,
    analyze_temporal_dimensions,
    calculate_rolling_metrics,
    compare_high_demand_time_series,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sample_df() -> pd.DataFrame:
    np.random.seed(42)
    n = 500
    dates = pd.date_range("2024-01-01", periods=n, freq="D")
    return pd.DataFrame({
        "ride_id": [f"R-{i:06d}" for i in range(n)],
        "city": np.random.choice(["Mumbai", "Delhi", "Bangalore"], n),
        "request_timestamp": dates,
        "was_accepted": np.random.choice([True, False], n, p=[0.8, 0.2]),
        "ride_completed": np.random.choice([True, False], n, p=[0.7, 0.3]),
        "rider_cancelled": np.random.choice([True, False], n, p=[0.1, 0.9]),
        "wait_time_minutes": np.random.uniform(2, 30, n),
        "surge_multiplier": np.random.uniform(1, 3, n),
        "is_high_demand": np.random.choice([True, False], n, p=[0.3, 0.7]),
        "is_weekend": np.random.choice([True, False], n),
        "time_period": np.random.choice(["morning", "afternoon", "evening", "night"], n),
        "hour_of_day": np.random.randint(0, 24, n),
    })


# ---------------------------------------------------------------------------
# Time aggregation
# ---------------------------------------------------------------------------

class TestTimeAggregation:
    def test_daily(self) -> None:
        df = _sample_df()
        result = aggregate_time_series(df, grain="day")
        assert len(result) > 0
        assert "request_timestamp_day" in result.columns

    def test_hourly(self) -> None:
        df = _sample_df()
        result = aggregate_time_series(df, grain="hour")
        assert len(result) > 0

    def test_weekly(self) -> None:
        df = _sample_df()
        result = aggregate_time_series(df, grain="week")
        assert len(result) > 0

    def test_grouped(self) -> None:
        df = _sample_df()
        result = aggregate_time_series(df, grain="day", group_columns=["city"])
        assert "city" in result.columns


# ---------------------------------------------------------------------------
# Rolling metrics
# ---------------------------------------------------------------------------

class TestRollingMetrics:
    def test_rolling(self) -> None:
        df = _sample_df()
        result = calculate_rolling_metrics(df, window=7)
        assert len(result) > 0

    def test_rolling_columns(self) -> None:
        df = _sample_df()
        result = calculate_rolling_metrics(df, window=7)
        rolling_cols = [c for c in result.columns if "rolling" in c]
        assert len(rolling_cols) > 0

    def test_rolling_grouped(self) -> None:
        df = _sample_df()
        result = calculate_rolling_metrics(df, window=7, group_columns=["city"])
        assert "city" in result.columns


# ---------------------------------------------------------------------------
# City time series
# ---------------------------------------------------------------------------

class TestCityTimeSeries:
    def test_city_time(self) -> None:
        df = _sample_df()
        result = analyze_city_time_series(df)
        assert "city" in result.columns
        assert len(result) > 0


# ---------------------------------------------------------------------------
# High-demand comparison
# ---------------------------------------------------------------------------

class TestHighDemand:
    def test_comparison(self) -> None:
        df = _sample_df()
        high, normal = compare_high_demand_time_series(df)
        assert len(high) > 0
        assert len(normal) > 0


# ---------------------------------------------------------------------------
# Temporal dimensions
# ---------------------------------------------------------------------------

class TestTemporalDimensions:
    def test_dimensions(self) -> None:
        df = _sample_df()
        results = analyze_temporal_dimensions(df)
        assert "weekday_weekend" in results
        assert "time_period" in results
        assert "hour_of_day" in results


# ---------------------------------------------------------------------------
# Missing timestamps
# ---------------------------------------------------------------------------

class TestMissingTimestamps:
    def test_missing_timestamp(self) -> None:
        df = _sample_df()
        df.loc[0, "request_timestamp"] = None
        result = aggregate_time_series(df, grain="day")
        assert len(result) > 0  # Should still work


# ---------------------------------------------------------------------------
# Empty data
# ---------------------------------------------------------------------------

class TestEmpty:
    def test_empty_df(self) -> None:
        df = pd.DataFrame()
        result = aggregate_time_series(df)
        assert len(result) == 0
