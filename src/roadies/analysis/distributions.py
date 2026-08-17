"""Distribution analysis functions for Roadies-CityRide.

Provides reusable analysis APIs for exploring feature distributions,
city-level comparisons, and high-demand vs normal-demand comparisons.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Numerical analysis
# ---------------------------------------------------------------------------

@dataclass
class NumericalStats:
    """Summary statistics for a numerical column."""

    column: str
    count: int
    mean: float
    median: float
    std: float
    min: float
    max: float
    q25: float
    q75: float


def compute_numerical_stats(df: pd.DataFrame, columns: list[str] | None = None) -> list[NumericalStats]:
    """Compute summary statistics for numerical columns.

    Parameters
    ----------
    df:
        The dataset to analyse.
    columns:
        Columns to analyse. If None, analyses all numeric columns.

    Returns
    -------
    list[NumericalStats]
        Summary statistics for each column.
    """
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()

    results: list[NumericalStats] = []
    for col in columns:
        if col not in df.columns:
            continue
        series = df[col].dropna()
        if len(series) == 0:
            continue
        results.append(NumericalStats(
            column=col,
            count=len(series),
            mean=float(series.mean()),
            median=float(series.median()),
            std=float(series.std()),
            min=float(series.min()),
            max=float(series.max()),
            q25=float(series.quantile(0.25)),
            q75=float(series.quantile(0.75)),
        ))
    return results


# ---------------------------------------------------------------------------
# Categorical analysis
# ---------------------------------------------------------------------------

@dataclass
class CategoricalStats:
    """Frequency distribution for a categorical column."""

    column: str
    total: int
    categories: dict[str, int] = field(default_factory=dict)
    percentages: dict[str, float] = field(default_factory=dict)


def compute_categorical_stats(df: pd.DataFrame, columns: list[str] | None = None) -> list[CategoricalStats]:
    """Compute frequency distributions for categorical columns.

    Parameters
    ----------
    df:
        The dataset to analyse.
    columns:
        Columns to analyse. If None, analyses all object/category columns.

    Returns
    -------
    list[CategoricalStats]
        Frequency distributions for each column.
    """
    if columns is None:
        columns = df.select_dtypes(include=["object", "category"]).columns.tolist()

    results: list[CategoricalStats] = []
    for col in columns:
        if col not in df.columns:
            continue
        total = len(df)
        counts = df[col].value_counts().to_dict()
        pcts = {k: round(v / total * 100, 2) if total > 0 else 0.0 for k, v in counts.items()}
        results.append(CategoricalStats(
            column=col,
            total=total,
            categories={str(k): int(v) for k, v in counts.items()},
            percentages={str(k): float(v) for k, v in pcts.items()},
        ))
    return results


# ---------------------------------------------------------------------------
# High-demand comparison
# ---------------------------------------------------------------------------

@dataclass
class HighDemandComparison:
    """Comparison of metrics between normal and high demand."""

    metric: str
    normal_mean: float
    high_mean: float
    normal_median: float
    high_median: float
    difference_pct: float


def compare_high_demand(
    df: pd.DataFrame,
    metrics: list[str] | None = None,
) -> list[HighDemandComparison]:
    """Compare metrics between normal and high demand periods.

    Parameters
    ----------
    df:
        Dataset with 'is_high_demand' column.
    metrics:
        Metrics to compare. If None, uses default operational metrics.

    Returns
    -------
    list[HighDemandComparison]
        Comparison results for each metric.
    """
    if "is_high_demand" not in df.columns:
        return []

    if metrics is None:
        metrics = [
            "surge_multiplier", "wait_time_minutes", "trip_duration_minutes",
            "driver_acceptance_rate", "city_hour_available_drivers",
            "city_hour_requested_rides",
        ]

    normal = df[df["is_high_demand"] == False]
    high = df[df["is_high_demand"] == True]

    results: list[HighDemandComparison] = []
    for metric in metrics:
        if metric not in df.columns:
            continue
        if not pd.api.types.is_numeric_dtype(df[metric]):
            continue

        n_mean = float(normal[metric].mean()) if len(normal) > 0 else 0.0
        h_mean = float(high[metric].mean()) if len(high) > 0 else 0.0
        n_med = float(normal[metric].median()) if len(normal) > 0 else 0.0
        h_med = float(high[metric].median()) if len(high) > 0 else 0.0

        diff_pct = ((h_mean - n_mean) / n_mean * 100) if n_mean != 0 else 0.0

        results.append(HighDemandComparison(
            metric=metric,
            normal_mean=round(n_mean, 4),
            high_mean=round(h_mean, 4),
            normal_median=round(n_med, 4),
            high_median=round(h_med, 4),
            difference_pct=round(diff_pct, 2),
        ))
    return results


# ---------------------------------------------------------------------------
# City-level comparison
# ---------------------------------------------------------------------------

@dataclass
class CityComparison:
    """City-level metric summary."""

    city: str
    metric: str
    count: int
    mean: float
    median: float


def compare_cities(
    df: pd.DataFrame,
    metrics: list[str] | None = None,
) -> list[CityComparison]:
    """Compare metrics across cities.

    Parameters
    ----------
    df:
        Dataset with 'city' column.
    metrics:
        Metrics to compare. If None, uses default metrics.

    Returns
    -------
    list[CityComparison]
        City-level summary for each metric.
    """
    if "city" not in df.columns:
        return []

    if metrics is None:
        metrics = [
            "surge_multiplier", "wait_time_minutes",
            "driver_acceptance_rate",
        ]

    results: list[CityComparison] = []
    for city in df["city"].unique():
        city_df = df[df["city"] == city]
        for metric in metrics:
            if metric not in city_df.columns:
                continue
            if not pd.api.types.is_numeric_dtype(city_df[metric]):
                continue
            series = city_df[metric].dropna()
            if len(series) == 0:
                continue
            results.append(CityComparison(
                city=str(city),
                metric=metric,
                count=len(series),
                mean=float(series.mean()),
                median=float(series.median()),
            ))
    return results
