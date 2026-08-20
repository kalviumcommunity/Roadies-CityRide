"""Business visualisation layer for Roadies-CityRide.

Provides reusable Plotly chart functions for communicating key operational findings.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ---------------------------------------------------------------------------
# City performance comparison
# ---------------------------------------------------------------------------

def plot_city_metric(
    df: pd.DataFrame,
    metric: str,
    title: str | None = None,
    sort_descending: bool = True,
) -> go.Figure:
    """Plot city comparison for a selected metric.

    Parameters
    ----------
    df:
        DataFrame with 'city' and metric columns.
    metric:
        Column name to plot.
    title:
        Chart title.
    sort_descending:
        Whether to sort bars descending.

    Returns
    -------
    go.Figure
        Plotly figure.
    """
    plot_df = df.sort_values(metric, ascending=not sort_descending)

    fig = px.bar(
        plot_df,
        x="city",
        y=metric,
        title=title or f"City Comparison: {metric}",
        labels={"city": "City", metric: metric.replace("_", " ").title()},
        color="city",
        color_discrete_sequence=px.colors.qualitative.Set2,
    )

    fig.update_layout(
        showlegend=False,
        xaxis_title="City",
        yaxis_title=metric.replace("_", " ").title(),
    )

    return fig


# ---------------------------------------------------------------------------
# High-demand impact
# ---------------------------------------------------------------------------

def plot_demand_impact(
    df: pd.DataFrame,
    metrics: list[str] | None = None,
    title: str = "Normal vs High Demand Impact",
) -> go.Figure:
    """Plot normal vs high-demand comparison for selected metrics.

    Parameters
    ----------
    df:
        DataFrame with 'demand_period' and metric columns.
    metrics:
        Metrics to compare.
    title:
        Chart title.

    Returns
    -------
    go.Figure
        Plotly figure.
    """
    if metrics is None:
        metrics = ["acceptance_rate", "rider_cancel_rate", "avg_wait_time", "avg_surge"]

    # Melt for grouped bar chart
    plot_df = df.melt(
        id_vars=["demand_period"],
        value_vars=metrics,
        var_name="metric",
        value_name="value",
    )

    fig = px.bar(
        plot_df,
        x="metric",
        y="value",
        color="demand_period",
        barmode="group",
        title=title,
        labels={
            "metric": "Metric",
            "value": "Value",
            "demand_period": "Demand Period",
        },
        color_discrete_map={"normal": "#2ecc71", "high": "#e74c3c"},
    )

    fig.update_layout(
        xaxis_title="Metric",
        yaxis_title="Value",
        legend_title="Demand Period",
    )

    return fig


# ---------------------------------------------------------------------------
# Demand/supply relationship
# ---------------------------------------------------------------------------

def plot_demand_supply_relationship(
    df: pd.DataFrame,
    x_metric: str = "demand_supply_ratio",
    y_metric: str = "surge_multiplier",
    color_metric: str | None = "city",
    title: str = "Demand/Supply vs Surge Relationship",
) -> go.Figure:
    """Plot demand/supply relationship as scatter/bubble.

    Parameters
    ----------
    df:
        Dataset.
    x_metric:
        X-axis metric.
    y_metric:
        Y-axis metric.
    color_metric:
        Color grouping metric.
    title:
        Chart title.

    Returns
    -------
    go.Figure
        Plotly figure.
    """
    fig = px.scatter(
        df,
        x=x_metric,
        y=y_metric,
        color=color_metric,
        title=title,
        labels={
            x_metric: x_metric.replace("_", " ").title(),
            y_metric: y_metric.replace("_", " ").title(),
        },
        opacity=0.6,
        color_discrete_sequence=px.colors.qualitative.Set2,
    )

    fig.update_layout(
        xaxis_title=x_metric.replace("_", " ").title(),
        yaxis_title=y_metric.replace("_", " ").title(),
    )

    return fig


# ---------------------------------------------------------------------------
# City deterioration
# ---------------------------------------------------------------------------

def plot_city_deterioration(
    df: pd.DataFrame,
    metric: str = "cancel_change",
    title: str = "City Deterioration During High Demand",
) -> go.Figure:
    """Plot city deterioration metrics.

    Parameters
    ----------
    df:
        DataFrame with city deterioration results.
    metric:
        Deterioration metric to plot.
    title:
        Chart title.

    Returns
    -------
    go.Figure
        Plotly figure.
    """
    plot_df = df.sort_values(metric, ascending=False)

    fig = px.bar(
        plot_df,
        x="city",
        y=metric,
        title=title,
        labels={
            "city": "City",
            metric: metric.replace("_", " ").title(),
        },
        color=metric,
        color_continuous_scale="RdYlGn_r",
    )

    fig.update_layout(
        xaxis_title="City",
        yaxis_title=metric.replace("_", " ").title(),
        showlegend=False,
    )

    return fig


# ---------------------------------------------------------------------------
# Temporal pattern
# ---------------------------------------------------------------------------

def plot_temporal_pattern(
    df: pd.DataFrame,
    time_col: str = "ride_hour",
    metrics: list[str] | None = None,
    title: str = "Operational Patterns by Time",
) -> go.Figure:
    """Plot temporal operational patterns.

    Parameters
    ----------
    df:
        Time-aggregated DataFrame.
    time_col:
        Time column for x-axis.
    metrics:
        Metrics to plot as lines.
    title:
        Chart title.

    Returns
    -------
    go.Figure
        Plotly figure.
    """
    if metrics is None:
        metrics = ["acceptance_rate", "rider_cancel_rate"]

    fig = go.Figure()

    colors = ["#3498db", "#e74c3c", "#2ecc71", "#f39c12"]

    for i, metric in enumerate(metrics):
        if metric in df.columns:
            fig.add_trace(go.Scatter(
                x=df[time_col],
                y=df[metric],
                mode="lines+markers",
                name=metric.replace("_", " ").title(),
                line=dict(color=colors[i % len(colors)], width=2),
            ))

    fig.update_layout(
        title=title,
        xaxis_title=time_col.replace("_", " ").title(),
        yaxis_title="Value",
        legend_title="Metric",
    )

    return fig


# ---------------------------------------------------------------------------
# City performance heatmap
# ---------------------------------------------------------------------------

def plot_city_heatmap(
    df: pd.DataFrame,
    metrics: list[str] | None = None,
    title: str = "City Performance Heatmap",
) -> go.Figure:
    """Plot city performance as heatmap.

    Parameters
    ----------
    df:
        DataFrame with city and metric columns.
    metrics:
        Metrics to include.
    title:
        Chart title.

    Returns
    -------
    go.Figure
        Plotly figure.
    """
    if metrics is None:
        metrics = ["acceptance_rate", "completion_rate", "rider_cancel_rate",
                    "avg_wait_time", "avg_surge"]

    # Filter to available metrics
    available = [m for m in metrics if m in df.columns]
    plot_df = df.set_index("city")[available]

    fig = px.imshow(
        plot_df,
        title=title,
        labels=dict(x="Metric", y="City", color="Value"),
        color_continuous_scale="RdYlGn",
        aspect="auto",
    )

    fig.update_layout(
        xaxis_title="Metric",
        yaxis_title="City",
    )

    return fig
