"""Time-series trend and rolling metrics analysis for Roadies-CityRide.

Provides reusable APIs for temporal analysis of ride-level data.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class TimeSeriesResult:
    """Result of time-series aggregation."""

    grain: str
    metrics: dict[str, list] = None  # type: ignore[assignment]
    group_columns: list[str] | None = None

    def __post_init__(self) -> None:
        if self.metrics is None:
            self.metrics = {}


# ---------------------------------------------------------------------------
# Default metrics
# ---------------------------------------------------------------------------

DEFAULT_TS_METRICS: dict[str, str] = {
    "ride_id": "count",
    "was_accepted": "mean",
    "ride_completed": "mean",
    "rider_cancelled": "mean",
    "driver_cancelled": "mean",
    "wait_time_minutes": "mean",
    "surge_multiplier": "mean",
    "base_fare": "mean",
    "demand_supply_ratio": "mean",
}


# ---------------------------------------------------------------------------
# Time aggregation
# ---------------------------------------------------------------------------

def aggregate_time_series(
    df: pd.DataFrame,
    timestamp_col: str = "request_timestamp",
    grain: Literal["hour", "day", "week"] = "day",
    group_columns: list[str] | None = None,
    metrics: dict[str, str] | None = None,
) -> pd.DataFrame:
    """Aggregate metrics by time grain.

    Parameters
    ----------
    df:
        Dataset with timestamp column.
    timestamp_col:
        Name of timestamp column.
    grain:
        Time grain: 'hour', 'day', or 'week'.
    group_columns:
        Additional columns to group by (e.g., ['city']).
    metrics:
        Metric aggregations.

    Returns
    -------
    pd.DataFrame
        Time-series aggregation.
    """
    if metrics is None:
        metrics = DEFAULT_TS_METRICS

    if timestamp_col not in df.columns:
        return pd.DataFrame()

    # Convert to datetime if needed
    ts = df[timestamp_col]
    if not pd.api.types.is_datetime64_any_dtype(ts):
        ts = pd.to_datetime(ts, errors="coerce", utc=True)

    work = df.copy()
    work["_ts"] = ts

    # Create time column
    if grain == "hour":
        work["_time"] = work["_ts"].dt.floor("h")
    elif grain == "day":
        work["_time"] = work["_ts"].dt.floor("D")
    elif grain == "week":
        work["_time"] = work["_ts"].dt.to_period("W").dt.start_time
    else:
        raise ValueError(f"Unsupported grain: {grain}")

    # Group columns
    group_cols = ["_time"]
    if group_columns:
        group_cols.extend(c for c in group_columns if c in work.columns)

    # Filter to available metrics
    available = {k: v for k, v in metrics.items() if k in work.columns}

    result = work.groupby(group_cols).agg(available).reset_index()

    # Rename _time to readable name
    result = result.rename(columns={"_time": f"{timestamp_col}_{grain}"})

    return result


def calculate_rolling_metrics(
    df: pd.DataFrame,
    timestamp_col: str = "request_timestamp",
    grain: Literal["hour", "day", "week"] = "day",
    window: int = 7,
    group_columns: list[str] | None = None,
    metrics: dict[str, str] | None = None,
) -> pd.DataFrame:
    """Calculate rolling metrics over a time window.

    Parameters
    ----------
    df:
        Dataset with timestamp column.
    timestamp_col:
        Name of timestamp column.
    grain:
        Time grain for aggregation.
    window:
        Rolling window size.
    group_columns:
        Additional columns to group by.
    metrics:
        Metrics to calculate rolling averages for.

    Returns
    -------
    pd.DataFrame
        Rolling metrics.
    """
    if metrics is None:
        metrics = {
            "was_accepted": "mean",
            "rider_cancelled": "mean",
            "wait_time_minutes": "mean",
            "surge_multiplier": "mean",
        }

    agg = aggregate_time_series(df, timestamp_col, grain, group_columns, metrics)
    if agg.empty:
        return agg

    # Find numeric columns to roll
    time_col = [c for c in agg.columns if c.startswith(timestamp_col)][0]
    group_cols = [time_col] + ([c for c in (group_columns or []) if c in agg.columns])

    # Sort by time
    agg = agg.sort_values(group_cols)

    # Calculate rolling for numeric columns
    numeric_cols = agg.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if col in group_cols:
            continue
        roll_col = f"{col}_rolling_{window}"
        if group_columns:
            agg[roll_col] = (
                agg.groupby([c for c in group_columns if c in agg.columns])[col]
                .transform(lambda x: x.rolling(window, min_periods=1).mean())
            )
        else:
            agg[roll_col] = agg[col].rolling(window, min_periods=1).mean()

    return agg


# ---------------------------------------------------------------------------
# City-level time series
# ---------------------------------------------------------------------------

def analyze_city_time_series(
    df: pd.DataFrame,
    timestamp_col: str = "request_timestamp",
    grain: Literal["hour", "day", "week"] = "day",
    metrics: dict[str, str] | None = None,
) -> pd.DataFrame:
    """Analyse time-series trends by city.

    Parameters
    ----------
    df:
        Dataset.
    timestamp_col:
        Timestamp column name.
    grain:
        Time grain.
    metrics:
        Metrics to aggregate.

    Returns
    -------
    pd.DataFrame
        City-level time-series aggregation.
    """
    if "city" not in df.columns:
        return pd.DataFrame()

    return aggregate_time_series(
        df, timestamp_col, grain, group_columns=["city"], metrics=metrics
    )


# ---------------------------------------------------------------------------
# High-demand comparison
# ---------------------------------------------------------------------------

def compare_high_demand_time_series(
    df: pd.DataFrame,
    timestamp_col: str = "request_timestamp",
    grain: Literal["hour", "day", "week"] = "day",
    demand_col: str = "is_high_demand",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compare time-series between high-demand and normal-demand periods.

    Parameters
    ----------
    df:
        Dataset with demand classification.
    timestamp_col:
        Timestamp column.
    grain:
        Time grain.
    demand_col:
        Column indicating high demand.

    Returns
    -------
    tuple[pd.DataFrame, pd.DataFrame]
        High-demand and normal-demand time-series.
    """
    if demand_col not in df.columns:
        return pd.DataFrame(), pd.DataFrame()

    high = df[df[demand_col] == True]
    normal = df[df[demand_col] == False]

    return (
        aggregate_time_series(high, timestamp_col, grain),
        aggregate_time_series(normal, timestamp_col, grain),
    )


# ---------------------------------------------------------------------------
# Temporal dimension analysis
# ---------------------------------------------------------------------------

def analyze_temporal_dimensions(
    df: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """Analyse temporal dimensions: weekday/weekend, time period, hour.

    Returns
    -------
    dict[str, pd.DataFrame]
        Analysis results keyed by dimension name.
    """
    results: dict[str, pd.DataFrame] = {}

    metrics = {
        "ride_id": "count",
        "was_accepted": "mean",
        "rider_cancelled": "mean",
        "wait_time_minutes": "mean",
        "surge_multiplier": "mean",
    }

    # Weekday vs weekend
    if "is_weekend" in df.columns:
        results["weekday_weekend"] = (
            df.groupby("is_weekend")
            .agg(metrics)
            .reset_index()
        )

    # Time period
    if "time_period" in df.columns:
        results["time_period"] = (
            df.groupby("time_period")
            .agg(metrics)
            .reset_index()
        )

    # Hour of day
    if "hour_of_day" in df.columns:
        results["hour_of_day"] = (
            df.groupby("hour_of_day")
            .agg(metrics)
            .reset_index()
        )

    return results
