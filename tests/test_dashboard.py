"""Tests for dashboard data loading and filtering."""

from __future__ import annotations

import pandas as pd
import pytest

from dashboard.data_loader import filter_dataframe


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sample_df() -> pd.DataFrame:
    return pd.DataFrame({
        "city": ["Mumbai", "Delhi", "Bangalore", "Mumbai", "Delhi"],
        "was_accepted": [True, False, True, True, False],
        "rider_cancelled": [False, True, False, False, True],
        "wait_time_minutes": [5, 10, 8, 12, 15],
        "surge_multiplier": [1.2, 2.5, 1.5, 1.8, 3.0],
        "is_high_demand": [False, True, False, True, True],
        "demand_category": ["normal", "high", "normal", "high", "high"],
    })


# ---------------------------------------------------------------------------
# Filter tests
# ---------------------------------------------------------------------------

class TestFilterDataframe:
    def test_no_filter(self) -> None:
        df = _sample_df()
        result = filter_dataframe(df)
        assert len(result) == 5

    def test_city_filter(self) -> None:
        df = _sample_df()
        result = filter_dataframe(df, cities=["Mumbai"])
        assert len(result) == 2
        assert all(result["city"] == "Mumbai")

    def test_high_demand_filter(self) -> None:
        df = _sample_df()
        result = filter_dataframe(df, high_demand_only=True)
        assert len(result) == 3
        assert all(result["is_high_demand"])

    def test_normal_demand_filter(self) -> None:
        df = _sample_df()
        result = filter_dataframe(df, high_demand_only=False)
        assert len(result) == 2
        assert not any(result["is_high_demand"])

    def test_surge_range(self) -> None:
        df = _sample_df()
        result = filter_dataframe(df, min_surge=2.0, max_surge=3.0)
        assert len(result) == 2
        assert all(result["surge_multiplier"] >= 2.0)

    def test_empty_df(self) -> None:
        df = pd.DataFrame()
        result = filter_dataframe(df, cities=["Mumbai"])
        assert len(result) == 0

    def test_no_match(self) -> None:
        df = _sample_df()
        result = filter_dataframe(df, cities=["Chennai"])
        assert len(result) == 0
