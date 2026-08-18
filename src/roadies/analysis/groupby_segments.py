"""GroupBy aggregation and segment insights for Roadies-CityRide.

Provides reusable APIs for grouped analysis of ride-level data
across business dimensions.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MIN_SEGMENT_SIZE = 100  # Minimum observations for business interpretation


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class SegmentRanking:
    """Ranking of segments for a specific metric."""

    metric: str
    ascending: bool
    rankings: list[tuple[str, float]] = field(default_factory=list)


@dataclass
class SegmentInsight:
    """A meaningful segment difference."""

    description: str
    segment: str
    metric: str
    value: float
    comparison: str


# ---------------------------------------------------------------------------
# Default metrics
# ---------------------------------------------------------------------------

DEFAULT_METRICS: dict[str, str] = {
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
# Core GroupBy functions
# ---------------------------------------------------------------------------

def aggregate_by_segment(
    df: pd.DataFrame,
    group_columns: list[str],
    metrics: dict[str, str] | None = None,
    min_size: int = MIN_SEGMENT_SIZE,
) -> pd.DataFrame:
    """Aggregate metrics by one or more grouping columns.

    Parameters
    ----------
    df:
        Dataset to aggregate.
    group_columns:
        Columns to group by.
    metrics:
        Metric aggregations. Keys are column names, values are aggregation functions.
    min_size:
        Minimum segment size for business interpretation.

    Returns
    -------
    pd.DataFrame
        Aggregated results with segment_size column.
    """
    if metrics is None:
        metrics = DEFAULT_METRICS

    # Filter to available columns
    available = {k: v for k, v in metrics.items() if k in df.columns}
    available_groups = [c for c in group_columns if c in df.columns]

    if not available_groups or not available:
        return pd.DataFrame()

    result = df.groupby(available_groups).agg(available).reset_index()

    # Add segment size
    size_col = df.groupby(available_groups).size().reset_index(name="segment_size")
    result = result.merge(size_col, on=available_groups, how="left")

    # Flatten column names
    rename_map = {}
    for col in result.columns:
        if col not in available_groups and col != "segment_size":
            if isinstance(col, tuple):
                rename_map[col] = f"{col[0]}_{col[1]}"
    if rename_map:
        result = result.rename(columns=rename_map)

    return result


def compare_segments(
    df: pd.DataFrame,
    group_columns: list[str],
    metrics: dict[str, str] | None = None,
    min_size: int = MIN_SEGMENT_SIZE,
) -> tuple[pd.DataFrame, list[SegmentInsight]]:
    """Compare segments and identify meaningful differences.

    Returns
    -------
    tuple[pd.DataFrame, list[SegmentInsight]]
        Aggregated segment data and insights.
    """
    agg = aggregate_by_segment(df, group_columns, metrics, min_size)

    if agg.empty:
        return agg, []

    insights: list[SegmentInsight] = []

    # Find segments with notable differences
    numeric_cols = agg.select_dtypes(include=[np.number]).columns
    metric_cols = [c for c in numeric_cols if c != "segment_size"]

    for metric in metric_cols:
        if metric not in agg.columns:
            continue

        # Filter to segments with sufficient size
        valid = agg[agg["segment_size"] >= min_size]
        if len(valid) < 2:
            continue

        mean_val = valid[metric].mean()
        for _, row in valid.iterrows():
            val = row[metric]
            if pd.isna(val):
                continue

            # Flag segments > 20% different from mean
            if mean_val != 0 and abs(val - mean_val) / abs(mean_val) > 0.20:
                segment_name = " / ".join(str(row[g]) for g in group_columns)
                direction = "higher" if val > mean_val else "lower"
                insights.append(SegmentInsight(
                    description=f"{segment_name} has {direction} {metric}",
                    segment=segment_name,
                    metric=metric,
                    value=float(val),
                    comparison=f"mean={mean_val:.3f}",
                ))

    return agg, insights


def rank_segments(
    df: pd.DataFrame,
    group_columns: list[str],
    metric: str,
    ascending: bool = True,
    min_size: int = MIN_SEGMENT_SIZE,
) -> SegmentRanking:
    """Rank segments by a specific metric.

    Parameters
    ----------
    df:
        Dataset.
    group_columns:
        Columns to group by.
    metric:
        Metric to rank by.
    ascending:
        If True, lowest values rank first.
    min_size:
        Minimum segment size.

    Returns
    -------
    SegmentRanking
        Ranked segments.
    """
    agg = aggregate_by_segment(df, group_columns, {metric: "mean" if metric != "ride_id" else "count"})

    if agg.empty:
        return SegmentRanking(metric=metric, ascending=ascending)

    # Filter to valid segments
    valid = agg[agg["segment_size"] >= min_size].copy()

    # Sort
    sort_col = f"{metric}_mean" if f"{metric}_mean" in valid.columns else metric
    if sort_col not in valid.columns:
        sort_col = metric

    valid = valid.sort_values(sort_col, ascending=ascending)

    # Build ranking
    rankings = []
    for _, row in valid.iterrows():
        segment_name = " / ".join(str(row[g]) for g in group_columns)
        rankings.append((segment_name, float(row[sort_col])))

    return SegmentRanking(metric=metric, ascending=ascending, rankings=rankings)
