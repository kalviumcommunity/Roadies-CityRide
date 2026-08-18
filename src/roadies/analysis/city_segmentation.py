"""City segmentation and comparison analysis for Roadies-CityRide.

Compares cities across operational and rider-experience metrics
and identifies meaningful behavioural profiles.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class CityProfile:
    """City-level profile with metrics and segment."""

    city: str
    ride_volume: int
    acceptance_rate: float
    rider_cancel_rate: float
    driver_cancel_rate: float
    completion_rate: float
    avg_wait: float
    median_wait: float
    avg_surge: float
    avg_demand_supply_ratio: float
    high_demand_share: float
    segment: str


@dataclass
class CityComparison:
    """Comparison of normal vs high demand for a city."""

    city: str
    metric: str
    normal_value: float
    high_value: float
    absolute_change: float
    relative_change_pct: float


@dataclass
class CityRanking:
    """Ranking of cities for a specific metric."""

    metric: str
    rankings: list[tuple[str, float]] = field(default_factory=list)


@dataclass
class CitySegmentationReport:
    """Full city segmentation report."""

    city_profiles: list[CityProfile] = field(default_factory=list)
    comparisons: list[CityComparison] = field(default_factory=list)
    rankings: list[CityRanking] = field(default_factory=list)

    def summary(self) -> str:
        lines = ["City Segmentation Report", f"Cities analysed: {len(self.city_profiles)}", ""]
        for p in self.city_profiles:
            lines.append(f"  {p.city}: {p.segment} (volume={p.ride_volume}, cancel={p.rider_cancel_rate:.1%})")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# City summary metrics
# ---------------------------------------------------------------------------

def compute_city_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Compute city-level summary metrics.

    Parameters
    ----------
    df:
        Dataset with engineered features.

    Returns
    -------
    pd.DataFrame
        City-level summary with one row per city.
    """
    agg_dict = {
        "ride_id": "count",
        "was_accepted": "mean",
        "rider_cancelled": "mean",
        "driver_cancelled": "mean",
        "ride_completed": "mean",
        "wait_time_minutes": ["mean", "median"],
        "surge_multiplier": "mean",
        "demand_supply_ratio": "mean",
    }

    # Only aggregate columns that exist
    available = {k: v for k, v in agg_dict.items() if k in df.columns}

    city_df = df.groupby("city").agg(available).reset_index()

    # Flatten column names
    city_df.columns = ["city"] + [
        f"{col[0]}_{col[1]}" if col[1] != "count" else col[0]
        for col in city_df.columns[1:]
    ]

    # Rename for consistency
    rename_map = {
        "ride_id": "ride_volume",
        "was_accepted_mean": "acceptance_rate",
        "rider_cancelled_mean": "rider_cancel_rate",
        "driver_cancelled_mean": "driver_cancel_rate",
        "ride_completed_mean": "completion_rate",
        "wait_time_minutes_mean": "avg_wait",
        "wait_time_minutes_median": "median_wait",
        "surge_multiplier_mean": "avg_surge",
        "demand_supply_ratio_mean": "avg_demand_supply_ratio",
    }
    city_df = city_df.rename(columns={k: v for k, v in rename_map.items() if k in city_df.columns})

    # High-demand share
    if "is_high_demand" in df.columns:
        hd_share = df.groupby("city")["is_high_demand"].mean().reset_index()
        hd_share.columns = ["city", "high_demand_share"]
        city_df = city_df.merge(hd_share, on="city", how="left")
    else:
        city_df["high_demand_share"] = 0.0

    return city_df


# ---------------------------------------------------------------------------
# High-demand vs normal comparison
# ---------------------------------------------------------------------------

def compare_normal_vs_high_demand(df: pd.DataFrame) -> list[CityComparison]:
    """Compare metrics between normal and high demand for each city.

    Parameters
    ----------
    df:
        Dataset with is_high_demand column.

    Returns
    -------
    list[CityComparison]
        City-level comparison results.
    """
    if "is_high_demand" not in df.columns:
        return []

    metrics = [
        ("was_accepted", "acceptance_rate"),
        ("rider_cancelled", "rider_cancel_rate"),
        ("surge_multiplier", "avg_surge"),
        ("wait_time_minutes", "avg_wait"),
        ("ride_completed", "completion_rate"),
    ]

    results: list[CityComparison] = []

    for city in df["city"].unique():
        city_df = df[df["city"] == city]
        normal = city_df[city_df["is_high_demand"] == False]
        high = city_df[city_df["is_high_demand"] == True]

        for col, label in metrics:
            if col not in city_df.columns:
                continue
            n_val = float(normal[col].mean()) if len(normal) > 0 else 0.0
            h_val = float(high[col].mean()) if len(high) > 0 else 0.0
            abs_change = h_val - n_val
            rel_change = (abs_change / n_val * 100) if n_val != 0 else 0.0

            results.append(CityComparison(
                city=str(city),
                metric=label,
                normal_value=round(n_val, 4),
                high_value=round(h_val, 4),
                absolute_change=round(abs_change, 4),
                relative_change_pct=round(rel_change, 2),
            ))

    return results


# ---------------------------------------------------------------------------
# Rankings
# ---------------------------------------------------------------------------

def rank_cities(df: pd.DataFrame, metrics: list[str] | None = None) -> list[CityRanking]:
    """Rank cities by specified metrics.

    Parameters
    ----------
    df:
        Dataset with city column.
    metrics:
        Metrics to rank by. If None, uses default metrics.

    Returns
    -------
    list[CityRanking]
        Rankings for each metric.
    """
    if metrics is None:
        metrics = [
            "rider_cancel_rate",
            "acceptance_rate",
            "avg_wait",
            "avg_surge",
            "completion_rate",
        ]

    city_summary = compute_city_summary(df)
    results: list[CityRanking] = []

    for metric in metrics:
        if metric not in city_summary.columns:
            continue

        # Sort: for cancel/surge/wait, lower is better (ascending=True)
        # for acceptance/completion, higher is better (ascending=False)
        ascending = metric in ("rider_cancel_rate", "avg_wait", "avg_surge")

        ranked = city_summary.sort_values(metric, ascending=ascending)
        rankings = [(str(row["city"]), float(row[metric])) for _, row in ranked.iterrows()]

        results.append(CityRanking(metric=metric, rankings=rankings))

    return results


# ---------------------------------------------------------------------------
# City segmentation
# ---------------------------------------------------------------------------

def segment_cities(df: pd.DataFrame) -> CitySegmentationReport:
    """Segment cities based on operational behaviour.

    Parameters
    ----------
    df:
        Dataset with engineered features.

    Returns
    -------
    CitySegmentationReport
        Full segmentation report with profiles, comparisons, rankings.
    """
    city_summary = compute_city_summary(df)

    # Classify cities
    def _classify(row: pd.Series) -> str:
        cancel = row.get("rider_cancel_rate", 0)
        surge = row.get("avg_surge", 1)
        wait = row.get("avg_wait", 5)
        acceptance = row.get("acceptance_rate", 0.8)

        if cancel > 0.15 and surge > 1.5:
            return "high-pressure"
        elif cancel > 0.12:
            return "cancellation-sensitive"
        elif surge > 1.5:
            return "surge-sensitive"
        elif acceptance < 0.75:
            return "demand-constrained"
        else:
            return "stable"

    profiles: list[CityProfile] = []
    for _, row in city_summary.iterrows():
        segment = _classify(row)
        profiles.append(CityProfile(
            city=str(row["city"]),
            ride_volume=int(row.get("ride_volume", 0)),
            acceptance_rate=float(row.get("acceptance_rate", 0)),
            rider_cancel_rate=float(row.get("rider_cancel_rate", 0)),
            driver_cancel_rate=float(row.get("driver_cancel_rate", 0)),
            completion_rate=float(row.get("completion_rate", 0)),
            avg_wait=float(row.get("avg_wait", 0)),
            median_wait=float(row.get("median_wait", 0)),
            avg_surge=float(row.get("avg_surge", 1)),
            avg_demand_supply_ratio=float(row.get("avg_demand_supply_ratio", 1)),
            high_demand_share=float(row.get("high_demand_share", 0)),
            segment=segment,
        ))

    comparisons = compare_normal_vs_high_demand(df)
    rankings = rank_cities(df)

    return CitySegmentationReport(
        city_profiles=profiles,
        comparisons=comparisons,
        rankings=rankings,
    )
