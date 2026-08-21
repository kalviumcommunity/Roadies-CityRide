"""Tests for KPI cards and summary metrics."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytest

from roadies.visualization.kpis import (
    Direction,
    KPI,
    KPICategory,
    KPISet,
    build_kpi_card_fig,
    build_kpi_cards,
    calculate_kpis,
    fmt_count,
    fmt_minutes,
    fmt_multiplier,
    fmt_pct,
    fmt_pp,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sample_df() -> pd.DataFrame:
    np.random.seed(42)
    n = 500
    return pd.DataFrame({
        "city": np.random.choice(["Mumbai", "Delhi", "Bangalore"], n),
        "was_accepted": np.random.choice([True, False], n, p=[0.8, 0.2]),
        "rider_cancelled": np.random.choice([True, False], n, p=[0.1, 0.9]),
        "was_completed": np.random.choice([True, False], n, p=[0.75, 0.25]),
        "wait_time_minutes": np.random.uniform(2, 30, n),
        "surge_multiplier": np.random.uniform(1, 3, n),
        "is_high_demand": np.random.choice([True, False], n, p=[0.3, 0.7]),
    })


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

class TestFormatting:
    def test_fmt_pct(self) -> None:
        assert fmt_pct(82.4) == "82.4%"
        assert fmt_pct(0.0) == "0.0%"

    def test_fmt_pp(self) -> None:
        assert fmt_pp(6.8) == "+6.8 pp"
        assert fmt_pp(-3.2) == "-3.2 pp"

    def test_fmt_minutes(self) -> None:
        assert fmt_minutes(11.2) == "11.2 min"

    def test_fmt_multiplier(self) -> None:
        assert fmt_multiplier(1.8) == "1.8x"

    def test_fmt_count(self) -> None:
        assert fmt_count(12430) == "12,430 rides"


# ---------------------------------------------------------------------------
# KPI calculation
# ---------------------------------------------------------------------------

class TestKPICalculation:
    def test_returns_kpiset(self) -> None:
        df = _sample_df()
        result = calculate_kpis(df)
        assert isinstance(result, KPISet)

    def test_overall_count(self) -> None:
        df = _sample_df()
        result = calculate_kpis(df)
        assert len(result.overall) >= 6

    def test_high_demand_count(self) -> None:
        df = _sample_df()
        result = calculate_kpis(df)
        assert len(result.high_demand) >= 3

    def test_city_count(self) -> None:
        df = _sample_df()
        result = calculate_kpis(df)
        assert len(result.city) == 3

    def test_deterministic(self) -> None:
        df = _sample_df()
        r1 = calculate_kpis(df)
        r2 = calculate_kpis(df)
        assert r1.overall[0].value == r2.overall[0].value


# ---------------------------------------------------------------------------
# Baseline comparison
# ---------------------------------------------------------------------------

class TestBaselineComparison:
    def test_high_demand_has_baseline(self) -> None:
        df = _sample_df()
        result = calculate_kpis(df)
        for kpi in result.high_demand:
            assert kpi.baseline is not None

    def test_city_has_baseline(self) -> None:
        df = _sample_df()
        result = calculate_kpis(df)
        for city_kpis in result.city.values():
            for kpi in city_kpis:
                assert kpi.baseline is not None


# ---------------------------------------------------------------------------
# Percentage-point calculations
# ---------------------------------------------------------------------------

class TestPercentagePointCalculations:
    def test_rate_differences_in_pp(self) -> None:
        df = _sample_df()
        result = calculate_kpis(df)
        for kpi in result.high_demand:
            if kpi.unit == "percent":
                assert kpi.comparison_unit == "pp"


# ---------------------------------------------------------------------------
# Direction
# ---------------------------------------------------------------------------

class TestDirection:
    def test_direction_is_enum(self) -> None:
        df = _sample_df()
        result = calculate_kpis(df)
        for kpi in result.overall:
            assert isinstance(kpi.direction, Direction)


# ---------------------------------------------------------------------------
# Missing values
# ---------------------------------------------------------------------------

class TestMissingValues:
    def test_empty_df(self) -> None:
        df = pd.DataFrame({
            "city": [],
            "was_accepted": [],
            "rider_cancelled": [],
            "wait_time_minutes": [],
            "surge_multiplier": [],
            "is_high_demand": [],
        })
        result = calculate_kpis(df)
        assert len(result.overall) >= 6


# ---------------------------------------------------------------------------
# Zero/empty datasets
# ---------------------------------------------------------------------------

class TestZeroEmpty:
    def test_single_row(self) -> None:
        df = pd.DataFrame({
            "city": ["Mumbai"],
            "was_accepted": [True],
            "rider_cancelled": [False],
            "was_completed": [True],
            "wait_time_minutes": [5.0],
            "surge_multiplier": [1.2],
            "is_high_demand": [False],
        })
        result = calculate_kpis(df)
        assert len(result.overall) >= 6


# ---------------------------------------------------------------------------
# City-level KPI support
# ---------------------------------------------------------------------------

class TestCityKPIs:
    def test_city_kpis_per_city(self) -> None:
        df = _sample_df()
        result = calculate_kpis(df)
        for city, kpis in result.city.items():
            assert len(kpis) >= 4
            for kpi in kpis:
                assert kpi.name in ["acceptance_rate", "rider_cancel_rate", "avg_wait_time", "avg_surge"]


# ---------------------------------------------------------------------------
# High-demand KPI support
# ---------------------------------------------------------------------------

class TestHighDemandKPIs:
    def test_high_demand_kpis(self) -> None:
        df = _sample_df()
        result = calculate_kpis(df)
        assert len(result.high_demand) >= 3


# ---------------------------------------------------------------------------
# KPI card visualisation
# ---------------------------------------------------------------------------

class TestKPICardVisualisation:
    def test_returns_figure(self) -> None:
        kpi = KPI(
            name="acceptance_rate", value=85.0, unit="percent",
            category=KPICategory.RIDER_EXPERIENCE, higher_is_better=True,
            label="Acceptance Rate", description="Test",
            formatted_value="85.0%",
        )
        fig = build_kpi_card_fig(kpi)
        assert isinstance(fig, go.Figure)

    def test_build_cards(self) -> None:
        kpis = [
            KPI(name="a", value=1.0, unit="x", category=KPICategory.OPERATIONAL,
                higher_is_better=True, label="A", description="", formatted_value="1.0x"),
        ]
        figs = build_kpi_cards(kpis)
        assert len(figs) == 1


# ---------------------------------------------------------------------------
# Integration
# ---------------------------------------------------------------------------

class TestIntegration:
    def test_full_workflow(self) -> None:
        df = _sample_df()
        result = calculate_kpis(df)

        # Build cards for overall
        cards = build_kpi_cards(result.overall)
        assert len(cards) >= 6

        # Build cards for high demand
        hd_cards = build_kpi_cards(result.high_demand)
        assert len(hd_cards) >= 3

        # Build cards for a city
        for city_kpis in result.city.values():
            city_cards = build_kpi_cards(city_kpis)
            assert len(city_cards) >= 4
