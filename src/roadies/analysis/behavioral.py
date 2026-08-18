"""Behavioural analysis and user segmentation for Roadies-CityRide.

Provides reusable APIs for rider and driver behavioural analysis
and rule-based segmentation.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MIN_RIDER_RIDES = 3  # Minimum rides for rider behavioural analysis
MIN_DRIVER_RIDES = 5  # Minimum rides for driver behavioural analysis


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class BehaviouralSegment:
    """A behavioural segment definition."""

    name: str
    description: str
    column: str
    threshold: float
    direction: str  # "above" or "below"


@dataclass
class SegmentSummary:
    """Summary metrics for a behavioural segment."""

    segment_type: str
    segment_name: str
    user_count: int
    ride_count: int
    cancellation_rate: float
    acceptance_rate: float
    completion_rate: float
    avg_wait: float
    avg_surge: float
    high_demand_share: float


# ---------------------------------------------------------------------------
# Rider behavioural analysis
# ---------------------------------------------------------------------------

def analyze_rider_behaviour(df: pd.DataFrame) -> pd.DataFrame:
    """Analyse rider-level behavioural patterns.

    Parameters
    ----------
    df:
        Ride-level dataset with rider_id.

    Returns
    -------
    pd.DataFrame
        Rider-level behavioural summary.
    """
    if "rider_id" not in df.columns:
        return pd.DataFrame()

    rider_stats = df.groupby("rider_id").agg(
        total_rides=("ride_id", "count"),
        cancelled_rides=("rider_cancelled", "sum"),
        completed_rides=("ride_completed", "sum"),
        avg_wait=("wait_time_minutes", "mean"),
        avg_surge=("surge_multiplier", "mean"),
        high_demand_rides=("is_high_demand", "sum") if "is_high_demand" in df.columns else ("ride_id", "count"),
        avg_demand_ratio=("demand_supply_ratio", "mean") if "demand_supply_ratio" in df.columns else ("ride_id", "count"),
    ).reset_index()

    rider_stats["cancellation_rate"] = rider_stats["cancelled_rides"] / rider_stats["total_rides"]
    rider_stats["completion_rate"] = rider_stats["completed_rides"] / rider_stats["total_rides"]

    if "is_high_demand" in df.columns:
        rider_stats["high_demand_share"] = rider_stats["high_demand_rides"] / rider_stats["total_rides"]

    return rider_stats


def segment_riders(
    df: pd.DataFrame,
    min_rides: int = MIN_RIDER_RIDES,
) -> pd.DataFrame:
    """Create rider behavioural segments based on observable behaviour.

    Segments (riders can belong to multiple):
    - cancellation_sensitive: cancellation_rate > 0.30
    - completion_oriented: completion_rate > 0.85
    - high_wait_exposure: avg_wait > 10 minutes
    - high_surge_exposure: avg_surge > 1.5
    - high_demand_exposed: high_demand_share > 0.40

    Parameters
    ----------
    df:
        Ride-level dataset.
    min_rides:
        Minimum rides for a rider to be segmented.

    Returns
    -------
    pd.DataFrame
        Rider-level data with segment columns.
    """
    rider = analyze_rider_behaviour(df)
    if rider.empty:
        return rider

    # Filter to riders with sufficient history
    rider = rider[rider["total_rides"] >= min_rides].copy()

    # Apply segment rules
    rider["cancellation_sensitive"] = rider["cancellation_rate"] > 0.30
    rider["completion_oriented"] = rider["completion_rate"] > 0.85
    rider["high_wait_exposure"] = rider["avg_wait"] > 10.0
    rider["high_surge_exposure"] = rider["avg_surge"] > 1.5

    if "high_demand_share" in rider.columns:
        rider["high_demand_exposed"] = rider["high_demand_share"] > 0.40

    return rider


def summarize_rider_segments(
    df: pd.DataFrame,
    min_rides: int = MIN_RIDER_RIDES,
) -> list[SegmentSummary]:
    """Summarize metrics for each rider behavioural segment.

    Parameters
    ----------
    df:
        Ride-level dataset.
    min_rides:
        Minimum rides threshold.

    Returns
    -------
    list[SegmentSummary]
        Segment summaries.
    """
    riders = segment_riders(df, min_rides)
    if riders.empty:
        return []

    summaries = []
    segment_cols = [
        "cancellation_sensitive",
        "completion_oriented",
        "high_wait_exposure",
        "high_surge_exposure",
    ]
    if "high_demand_exposed" in riders.columns:
        segment_cols.append("high_demand_exposed")

    for col in segment_cols:
        if col not in riders.columns:
            continue

        seg_riders = riders[riders[col] == True]
        if len(seg_riders) == 0:
            continue

        # Calculate aggregate metrics
        total_users = len(seg_riders)
        total_rides = seg_riders["total_rides"].sum()
        cancellation_rate = seg_riders["cancelled_rides"].sum() / total_rides if total_rides > 0 else 0
        completion_rate = seg_riders["completed_rides"].sum() / total_rides if total_rides > 0 else 0
        avg_wait = seg_riders["avg_wait"].mean()
        avg_surge = seg_riders["avg_surge"].mean()
        high_demand_share = seg_riders["high_demand_share"].mean() if "high_demand_share" in seg_riders.columns else 0

        summaries.append(SegmentSummary(
            segment_type="rider",
            segment_name=col,
            user_count=total_users,
            ride_count=int(total_rides),
            cancellation_rate=float(cancellation_rate),
            acceptance_rate=0,  # Not applicable for riders
            completion_rate=float(completion_rate),
            avg_wait=float(avg_wait),
            avg_surge=float(avg_surge),
            high_demand_share=float(high_demand_share),
        ))

    return summaries


# ---------------------------------------------------------------------------
# Driver behavioural analysis
# ---------------------------------------------------------------------------

def analyze_driver_behaviour(df: pd.DataFrame) -> pd.DataFrame:
    """Analyse driver-level behavioural patterns.

    Parameters
    ----------
    df:
        Ride-level dataset with driver_id.

    Returns
    -------
    pd.DataFrame
        Driver-level behavioural summary.
    """
    if "driver_id" not in df.columns:
        return pd.DataFrame()

    driver_stats = df.groupby("driver_id").agg(
        total_rides=("ride_id", "count"),
        accepted_rides=("was_accepted", "sum"),
        driver_cancelled=("driver_cancelled", "sum"),
        completed_rides=("ride_completed", "sum"),
        avg_wait=("wait_time_minutes", "mean"),
        avg_surge=("surge_multiplier", "mean"),
        high_demand_rides=("is_high_demand", "sum") if "is_high_demand" in df.columns else ("ride_id", "count"),
    ).reset_index()

    driver_stats["acceptance_rate"] = driver_stats["accepted_rides"] / driver_stats["total_rides"]
    driver_stats["driver_cancel_rate"] = driver_stats["driver_cancelled"] / driver_stats["total_rides"]
    driver_stats["completion_rate"] = driver_stats["completed_rides"] / driver_stats["total_rides"]

    if "is_high_demand" in df.columns:
        driver_stats["high_demand_share"] = driver_stats["high_demand_rides"] / driver_stats["total_rides"]

    return driver_stats


def segment_drivers(
    df: pd.DataFrame,
    min_rides: int = MIN_DRIVER_RIDES,
) -> pd.DataFrame:
    """Create driver behavioural segments based on observable behaviour.

    Segments (drivers can belong to multiple):
    - high_acceptance: acceptance_rate > 0.90
    - low_acceptance: acceptance_rate < 0.70
    - high_demand_resistant: high_demand_share > 0.40 AND acceptance_rate > 0.80
    - cancellation_prone: driver_cancel_rate > 0.15

    Parameters
    ----------
    df:
        Ride-level dataset.
    min_rides:
        Minimum rides for a driver to be segmented.

    Returns
    -------
    pd.DataFrame
        Driver-level data with segment columns.
    """
    drivers = analyze_driver_behaviour(df)
    if drivers.empty:
        return drivers

    # Filter to drivers with sufficient history
    drivers = drivers[drivers["total_rides"] >= min_rides].copy()

    # Apply segment rules
    drivers["high_acceptance"] = drivers["acceptance_rate"] > 0.90
    drivers["low_acceptance"] = drivers["acceptance_rate"] < 0.70
    drivers["cancellation_prone"] = drivers["driver_cancel_rate"] > 0.15

    if "high_demand_share" in drivers.columns:
        drivers["high_demand_resistant"] = (
            (drivers["high_demand_share"] > 0.40) & (drivers["acceptance_rate"] > 0.80)
        )

    return drivers


def summarize_driver_segments(
    df: pd.DataFrame,
    min_rides: int = MIN_DRIVER_RIDES,
) -> list[SegmentSummary]:
    """Summarize metrics for each driver behavioural segment.

    Parameters
    ----------
    df:
        Ride-level dataset.
    min_rides:
        Minimum rides threshold.

    Returns
    -------
    list[SegmentSummary]
        Segment summaries.
    """
    drivers = segment_drivers(df, min_rides)
    if drivers.empty:
        return []

    summaries = []
    segment_cols = [
        "high_acceptance",
        "low_acceptance",
        "cancellation_prone",
    ]
    if "high_demand_resistant" in drivers.columns:
        segment_cols.append("high_demand_resistant")

    for col in segment_cols:
        if col not in drivers.columns:
            continue

        segment_drivers_subset = drivers[drivers[col] == True]
        if len(segment_drivers_subset) == 0:
            continue

        total_users = len(segment_drivers_subset)
        total_rides = segment_drivers_subset["total_rides"].sum()
        acceptance_rate = segment_drivers_subset["accepted_rides"].sum() / total_rides if total_rides > 0 else 0
        driver_cancel_rate = segment_drivers_subset["driver_cancelled"].sum() / total_rides if total_rides > 0 else 0
        completion_rate = segment_drivers_subset["completed_rides"].sum() / total_rides if total_rides > 0 else 0
        avg_wait = segment_drivers_subset["avg_wait"].mean()
        avg_surge = segment_drivers_subset["avg_surge"].mean()
        high_demand_share = segment_drivers_subset["high_demand_share"].mean() if "high_demand_share" in segment_drivers_subset.columns else 0

        summaries.append(SegmentSummary(
            segment_type="driver",
            segment_name=col,
            user_count=total_users,
            ride_count=int(total_rides),
            cancellation_rate=float(driver_cancel_rate),
            acceptance_rate=float(acceptance_rate),
            completion_rate=float(completion_rate),
            avg_wait=float(avg_wait),
            avg_surge=float(avg_surge),
            high_demand_share=float(high_demand_share),
        ))

    return summaries


# ---------------------------------------------------------------------------
# High-demand comparison
# ---------------------------------------------------------------------------

def compare_behaviour_by_demand(
    df: pd.DataFrame,
    demand_col: str = "is_high_demand",
) -> dict[str, dict[str, dict[str, float]]]:
    """Compare rider and driver behaviour between normal and high-demand periods.

    Parameters
    ----------
    df:
        Ride-level dataset.
    demand_col:
        Column indicating high demand.

    Returns
    -------
    dict
        Behaviour comparison keyed by segment type, then demand period.
    """
    if demand_col not in df.columns:
        return {}

    results: dict[str, dict[str, dict[str, float]]] = {}

    for demand_val, label in [(True, "high"), (False, "normal")]:
        subset = df[df[demand_col] == demand_val]

        metrics = {
            "ride_count": len(subset),
            "rider_cancel_rate": subset["rider_cancelled"].mean() if "rider_cancelled" in subset.columns else 0,
            "driver_cancel_rate": subset["driver_cancelled"].mean() if "driver_cancelled" in subset.columns else 0,
            "acceptance_rate": subset["was_accepted"].mean() if "was_accepted" in subset.columns else 0,
            "completion_rate": subset["ride_completed"].mean() if "ride_completed" in subset.columns else 0,
            "avg_wait": subset["wait_time_minutes"].mean() if "wait_time_minutes" in subset.columns else 0,
            "avg_surge": subset["surge_multiplier"].mean() if "surge_multiplier" in subset.columns else 0,
        }

        results[label] = metrics

    # Calculate changes
    if "high" in results and "normal" in results:
        changes = {}
        for metric in results["high"]:
            high_val = results["high"][metric]
            normal_val = results["normal"][metric]
            if normal_val != 0:
                changes[metric] = (high_val - normal_val) / normal_val
            else:
                changes[metric] = 0
        results["change_pct"] = changes

    return results


# ---------------------------------------------------------------------------
# Repeated behaviour analysis
# ---------------------------------------------------------------------------

def analyze_repeated_behaviour(
    df: pd.DataFrame,
    min_rides: int = MIN_RIDER_RIDES,
) -> dict[str, pd.DataFrame]:
    """Analyse repeated behaviour patterns for riders and drivers.

    Parameters
    ----------
    df:
        Ride-level dataset.
    min_rides:
        Minimum rides for repeated behaviour analysis.

    Returns
    -------
    dict[str, pd.DataFrame]
        Repeated behaviour analysis for riders and drivers.
    """
    results: dict[str, pd.DataFrame] = {}

    # Rider repeated behaviour
    if "rider_id" in df.columns:
        rider_stats = analyze_rider_behaviour(df)
        if not rider_stats.empty:
            repeated_riders = rider_stats[rider_stats["total_rides"] >= min_rides].copy()
            repeated_riders["is_repeat_canceller"] = repeated_riders["cancellation_rate"] > 0.50
            repeated_riders["is_repeat_completer"] = repeated_riders["completion_rate"] > 0.90
            results["riders"] = repeated_riders

    # Driver repeated behaviour
    if "driver_id" in df.columns:
        driver_stats = analyze_driver_behaviour(df)
        if not driver_stats.empty:
            repeated_drivers = driver_stats[driver_stats["total_rides"] >= min_rides].copy()
            repeated_drivers["is_repeat_rejector"] = repeated_drivers["acceptance_rate"] < 0.50
            repeated_drivers["is_repeat_acceptor"] = repeated_drivers["acceptance_rate"] > 0.95
            results["drivers"] = repeated_drivers

    return results
