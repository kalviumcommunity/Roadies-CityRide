"""Correlation and relationship analysis for Roadies-CityRide.

Analyses relationships between operational variables and rider-experience
outcomes, with special focus on high-demand periods.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from scipy import stats

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class CorrelationResult:
    """Result of a correlation analysis."""

    var1: str
    var2: str
    method: str
    coefficient: float
    p_value: float
    sample_size: int
    significant: bool


@dataclass
class RelationshipReport:
    """Report of relationship analysis results."""

    correlations: list[CorrelationResult] = field(default_factory=list)
    high_demand_correlations: list[CorrelationResult] = field(default_factory=list)
    normal_demand_correlations: list[CorrelationResult] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            "Relationship Analysis Report",
            f"Total correlations: {len(self.correlations)}",
            f"High-demand correlations: {len(self.high_demand_correlations)}",
            f"Normal-demand correlations: {len(self.normal_demand_correlations)}",
            "",
            "Strongest relationships (|r| > 0.3):",
        ]
        for c in self.correlations:
            if abs(c.coefficient) > 0.3:
                lines.append(f"  {c.var1} <-> {c.var2}: {c.coefficient:.3f} ({c.method}, p={c.p_value:.4f})")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Correlation pairs to analyse
# ---------------------------------------------------------------------------

CONTINUOUS_PAIRS: list[tuple[str, str, str]] = [
    ("demand_supply_ratio", "surge_multiplier", "spearman"),
    ("demand_supply_ratio", "wait_time_minutes", "spearman"),
    ("demand_supply_ratio", "driver_acceptance_rate", "spearman"),
    ("surge_multiplier", "wait_time_minutes", "spearman"),
    ("surge_intensity", "wait_time_minutes", "spearman"),
    ("city_hour_requested_rides", "surge_multiplier", "spearman"),
]

BINARY_PAIRS: list[tuple[str, str]] = [
    ("surge_multiplier", "rider_cancelled"),
    ("driver_acceptance_rate", "rider_cancelled"),
    ("wait_time_minutes", "rider_cancelled"),
    ("driver_acceptance_rate", "ride_completed"),
    ("surge_multiplier", "ride_completed"),
]


# ---------------------------------------------------------------------------
# Core analysis functions
# ---------------------------------------------------------------------------

def _compute_correlation(
    df: pd.DataFrame,
    var1: str,
    var2: str,
    method: str = "spearman",
) -> CorrelationResult | None:
    """Compute correlation between two variables."""
    if var1 not in df.columns or var2 not in df.columns:
        return None

    clean = df[[var1, var2]].dropna()
    if len(clean) < 10:
        return None

    try:
        if method == "spearman":
            coeff, pval = stats.spearmanr(clean[var1], clean[var2])
        else:
            coeff, pval = stats.pearsonr(clean[var1], clean[var2])
    except Exception:
        return None

    return CorrelationResult(
        var1=var1,
        var2=var2,
        method=method,
        coefficient=float(coeff),
        p_value=float(pval),
        sample_size=len(clean),
        significant=pval < 0.05,
    )


def compute_correlations(df: pd.DataFrame) -> list[CorrelationResult]:
    """Compute correlations for all specified pairs.

    Parameters
    ----------
    df:
        The dataset to analyse.

    Returns
    -------
    list[CorrelationResult]
        Correlation results for each pair.
    """
    results: list[CorrelationResult] = []

    for var1, var2, method in CONTINUOUS_PAIRS:
        result = _compute_correlation(df, var1, var2, method)
        if result:
            results.append(result)

    # Binary pairs: use point-biserial (pearson on binary)
    for var1, var2 in BINARY_PAIRS:
        result = _compute_correlation(df, var1, var2, "pearson")
        if result:
            results.append(result)

    return results


def compare_relationships_by_demand(df: pd.DataFrame) -> tuple[list[CorrelationResult], list[CorrelationResult]]:
    """Compare correlations between normal and high demand.

    Returns
    -------
    tuple[list[CorrelationResult], list[CorrelationResult]]
        (high_demand_correlations, normal_demand_correlations)
    """
    if "is_high_demand" not in df.columns:
        return [], []

    high_df = df[df["is_high_demand"] == True]
    normal_df = df[df["is_high_demand"] == False]

    high_corr = compute_correlations(high_df)
    normal_corr = compute_correlations(normal_df)

    return high_corr, normal_corr


def compare_relationships_by_city(df: pd.DataFrame, var1: str, var2: str) -> list[CorrelationResult]:
    """Compare a relationship across cities.

    Parameters
    ----------
    df:
        The dataset to analyse.
    var1, var2:
        Variables to correlate.

    Returns
    -------
    list[CorrelationResult]
        City-level correlation results.
    """
    if "city" not in df.columns:
        return []

    results: list[CorrelationResult] = []
    for city in df["city"].unique():
        city_df = df[df["city"] == city]
        result = _compute_correlation(city_df, var1, var2, "spearman")
        if result:
            results.append(result)
    return results
