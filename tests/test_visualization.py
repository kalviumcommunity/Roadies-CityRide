"""Tests for business visualisation layer."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytest

from roadies.visualization import (
    plot_city_deterioration,
    plot_city_heatmap,
    plot_city_metric,
    plot_demand_impact,
    plot_demand_supply_relationship,
    plot_temporal_pattern,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sample_df() -> pd.DataFrame:
    np.random.seed(42)
    n = 200
    return pd.DataFrame({
        "city": np.random.choice(["Mumbai", "Delhi", "Bangalore"], n),
        "demand_supply_ratio": np.random.uniform(0.5, 2.0, n),
        "surge_multiplier": np.random.uniform(1, 3, n),
        "wait_time_minutes": np.random.uniform(2, 30, n),
        "acceptance_rate": np.random.uniform(70, 95, n),
        "rider_cancel_rate": np.random.uniform(5, 20, n),
        "is_high_demand": np.random.choice([True, False], n, p=[0.3, 0.7]),
    })


def _city_df() -> pd.DataFrame:
    return pd.DataFrame({
        "city": ["Mumbai", "Delhi", "Bangalore"],
        "acceptance_rate": [75.0, 80.0, 85.0],
        "rider_cancel_rate": [15.0, 12.0, 9.0],
        "avg_wait_time": [12.0, 10.0, 8.0],
        "avg_surge": [1.8, 1.5, 1.3],
    })


def _demand_df() -> pd.DataFrame:
    return pd.DataFrame({
        "demand_period": ["normal", "high"],
        "acceptance_rate": [85.0, 72.0],
        "rider_cancel_rate": [8.0, 15.0],
        "avg_wait_time": [7.0, 12.0],
        "avg_surge": [1.2, 1.8],
    })


def _deterioration_df() -> pd.DataFrame:
    return pd.DataFrame({
        "city": ["Mumbai", "Delhi", "Bangalore"],
        "cancel_change": [6.8, 4.5, 2.1],
        "acceptance_change": [-12.5, -8.0, -5.0],
        "wait_change": [5.0, 3.5, 2.0],
    })


def _hourly_df() -> pd.DataFrame:
    return pd.DataFrame({
        "ride_hour": list(range(24)),
        "acceptance_rate": np.random.uniform(70, 95, 24),
        "rider_cancel_rate": np.random.uniform(5, 20, 24),
    })


# ---------------------------------------------------------------------------
# Figure objects returned
# ---------------------------------------------------------------------------

class TestFigureObjects:
    def test_city_metric_returns_figure(self) -> None:
        df = _city_df()
        fig = plot_city_metric(df, "acceptance_rate")
        assert isinstance(fig, go.Figure)

    def test_demand_impact_returns_figure(self) -> None:
        df = _demand_df()
        fig = plot_demand_impact(df)
        assert isinstance(fig, go.Figure)


# ---------------------------------------------------------------------------
# Expected chart type
# ---------------------------------------------------------------------------

class TestChartTypes:
    def test_city_metric_is_bar(self) -> None:
        df = _city_df()
        fig = plot_city_metric(df, "acceptance_rate")
        assert fig.data[0].type == "bar"

    def test_demand_impact_is_bar(self) -> None:
        df = _demand_df()
        fig = plot_demand_impact(df)
        assert fig.data[0].type == "bar"


# ---------------------------------------------------------------------------
# Expected traces
# ---------------------------------------------------------------------------

class TestTraces:
    def test_demand_impact_traces(self) -> None:
        df = _demand_df()
        fig = plot_demand_impact(df, metrics=["acceptance_rate", "rider_cancel_rate"])
        assert len(fig.data) == 2  # normal + high


# ---------------------------------------------------------------------------
# Expected axis labels
# ---------------------------------------------------------------------------

class TestAxisLabels:
    def test_city_metric_labels(self) -> None:
        df = _city_df()
        fig = plot_city_metric(df, "acceptance_rate")
        assert fig.layout.xaxis.title.text == "City"
        assert fig.layout.yaxis.title.text == "Acceptance Rate"


# ---------------------------------------------------------------------------
# Expected titles
# ---------------------------------------------------------------------------

class TestTitles:
    def test_custom_title(self) -> None:
        df = _city_df()
        fig = plot_city_metric(df, "acceptance_rate", title="My Title")
        assert fig.layout.title.text == "My Title"


# ---------------------------------------------------------------------------
# Expected categories
# ---------------------------------------------------------------------------

class TestCategories:
    def test_city_categories(self) -> None:
        df = _city_df()
        fig = plot_city_metric(df, "acceptance_rate")
        # Plotly may create separate traces per city
        all_cities = set()
        for trace in fig.data:
            if trace.x is not None:
                all_cities.update(trace.x.tolist())
        assert all_cities == {"Mumbai", "Delhi", "Bangalore"}


# ---------------------------------------------------------------------------
# Empty data handling
# ---------------------------------------------------------------------------

class TestEmptyData:
    def test_empty_df(self) -> None:
        df = pd.DataFrame({"city": [], "acceptance_rate": []})
        fig = plot_city_metric(df, "acceptance_rate")
        assert isinstance(fig, go.Figure)


# ---------------------------------------------------------------------------
# High-demand representation
# ---------------------------------------------------------------------------

class TestHighDemand:
    def test_demand_impact_colors(self) -> None:
        df = _demand_df()
        fig = plot_demand_impact(df)
        colors = [trace.marker.color for trace in fig.data]
        assert "#2ecc71" in colors  # normal
        assert "#e74c3c" in colors  # high


# ---------------------------------------------------------------------------
# Generated dataset integration
# ---------------------------------------------------------------------------

class TestIntegration:
    def test_all_chart_functions(self) -> None:
        # City metric
        fig1 = plot_city_metric(_city_df(), "acceptance_rate")
        assert isinstance(fig1, go.Figure)

        # Demand impact
        fig2 = plot_demand_impact(_demand_df())
        assert isinstance(fig2, go.Figure)

        # Demand/supply relationship
        fig3 = plot_demand_supply_relationship(_sample_df())
        assert isinstance(fig3, go.Figure)

        # City deterioration
        fig4 = plot_city_deterioration(_deterioration_df())
        assert isinstance(fig4, go.Figure)

        # Temporal pattern
        fig5 = plot_temporal_pattern(_hourly_df())
        assert isinstance(fig5, go.Figure)

        # Heatmap
        fig6 = plot_city_heatmap(_city_df())
        assert isinstance(fig6, go.Figure)
