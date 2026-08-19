"""Anomaly detection and operational risk patterns for Roadies-CityRide.

Provides reusable APIs for identifying unusual city/time conditions
associated with elevated rider-experience risk.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

RISK_THRESHOLDS = {
    "demand_supply_ratio": {"elevated": 1.5, "high": 2.0, "critical": 2.5},
    "surge_multiplier": {"elevated": 1.5, "high": 2.0, "critical": 2.5},
    "wait_time_minutes": {"elevated": 10, "high": 15, "critical": 20},
    "rider_cancel_rate": {"elevated": 0.15, "high": 0.20, "critical": 0.25},
    "acceptance_rate": {"elevated": 0.75, "high": 0.70, "critical": 0.65},  # Lower is worse
    "completion_rate": {"elevated": 0.75, "high": 0.70, "critical": 0.65},  # Lower is worse
}

ZSCORE_THRESHOLD = 2.0
IQR_MULTIPLIER = 1.5
MIN_SAMPLES = 10


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Anomaly:
    """An identified anomaly."""

    metric: str
    value: float
    baseline: float
    deviation: float
    relative_deviation: float
    anomaly_type: str  # "global", "city_relative", "temporal"
    city: str | None = None
    severity: str = "elevated"


@dataclass
class RiskCondition:
    """A risk condition identified."""

    risk_level: str  # "normal", "elevated", "high", "critical"
    signals: list[str] = field(default_factory=list)
    metric_values: dict[str, float] = field(default_factory=dict)
    city: str | None = None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _detect_outliers_zscore(values: pd.Series, threshold: float = ZSCORE_THRESHOLD) -> pd.Series:
    """Detect outliers using z-score method."""
    mean_val = values.mean()
    std_val = values.std()
    if std_val == 0:
        return pd.Series(False, index=values.index)
    zscores = (values - mean_val) / std_val
    return zscores.abs() > threshold


def _detect_outliers_iqr(values: pd.Series, multiplier: float = IQR_MULTIPLIER) -> pd.Series:
    """Detect outliers using IQR method."""
    q1 = values.quantile(0.25)
    q3 = values.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - multiplier * iqr
    upper = q3 + multiplier * iqr
    return (values < lower) | (values > upper)


# ---------------------------------------------------------------------------
# Anomaly detection
# ---------------------------------------------------------------------------

def detect_anomalies(
    df: pd.DataFrame,
    metrics: list[str] | None = None,
    method: Literal["zscore", "iqr"] = "zscore",
) -> list[Anomaly]:
    """Detect global anomalies in operational metrics.

    Parameters
    ----------
    df:
        Dataset.
    metrics:
        Metrics to check for anomalies.
    method:
        Detection method: "zscore" or "iqr".

    Returns
    -------
    list[Anomaly]
        Detected anomalies.
    """
    if metrics is None:
        metrics = ["demand_supply_ratio", "surge_multiplier", "wait_time_minutes",
                    "rider_cancelled", "was_accepted", "ride_completed"]

    anomalies = []

    for metric in metrics:
        if metric not in df.columns:
            continue

        values = df[metric].dropna()
        if len(values) < MIN_SAMPLES:
            continue

        mean_val = values.mean()
        std_val = values.std()

        if method == "zscore":
            mask = _detect_outliers_zscore(values, threshold=ZSCORE_THRESHOLD)
        else:
            mask = _detect_outliers_iqr(values, multiplier=IQR_MULTIPLIER)

        # Get anomalous values
        anomalous = values[mask]

        for idx in anomalous.index:
            val = anomalous[idx]
            deviation = val - mean_val
            rel_deviation = deviation / mean_val if mean_val != 0 else 0

            anomalies.append(Anomaly(
                metric=metric,
                value=float(val),
                baseline=float(mean_val),
                deviation=float(deviation),
                relative_deviation=float(rel_deviation),
                anomaly_type="global",
                severity=_classify_severity(metric, val),
            ))

    return anomalies


def detect_city_relative_anomalies(
    df: pd.DataFrame,
    metrics: list[str] | None = None,
    city_col: str = "city",
) -> list[Anomaly]:
    """Detect anomalies relative to each city's baseline.

    Parameters
    ----------
    df:
        Dataset.
    metrics:
        Metrics to check.
    city_col:
        City column.

    Returns
    -------
    list[Anomaly]
        City-relative anomalies.
    """
    if metrics is None:
        metrics = ["demand_supply_ratio", "surge_multiplier", "wait_time_minutes",
                    "rider_cancelled", "was_accepted", "ride_completed"]

    anomalies = []

    for city, city_df in df.groupby(city_col):
        for metric in metrics:
            if metric not in city_df.columns:
                continue

            values = city_df[metric].dropna()
            if len(values) < MIN_SAMPLES:
                continue

            mean_val = values.mean()
            std_val = values.std()

            if std_val == 0:
                continue

            # Find values that are unusual for this city
            zscores = (values - mean_val) / std_val
            anomalous = values[zscores.abs() > ZSCORE_THRESHOLD]

            for idx in anomalous.index:
                val = anomalous[idx]
                deviation = val - mean_val
                rel_deviation = deviation / mean_val if mean_val != 0 else 0

                anomalies.append(Anomaly(
                    metric=metric,
                    value=float(val),
                    baseline=float(mean_val),
                    deviation=float(deviation),
                    relative_deviation=float(rel_deviation),
                    anomaly_type="city_relative",
                    city=str(city),
                    severity=_classify_severity(metric, val),
                ))

    return anomalies


def _classify_severity(metric: str, value: float) -> str:
    """Classify anomaly severity based on thresholds."""
    thresholds = RISK_THRESHOLDS.get(metric)
    if not thresholds:
        return "elevated"

    # For metrics where lower is worse (acceptance, completion)
    if metric in ["was_accepted", "ride_completed", "acceptance_rate", "completion_rate"]:
        if value <= thresholds["critical"]:
            return "critical"
        elif value <= thresholds["high"]:
            return "high"
        elif value <= thresholds["elevated"]:
            return "elevated"
    else:
        # For metrics where higher is worse
        if value >= thresholds["critical"]:
            return "critical"
        elif value >= thresholds["high"]:
            return "high"
        elif value >= thresholds["elevated"]:
            return "elevated"

    return "normal"


# ---------------------------------------------------------------------------
# Risk classification
# ---------------------------------------------------------------------------

def classify_risk(
    df: pd.DataFrame,
    thresholds: dict[str, dict[str, float]] | None = None,
) -> pd.DataFrame:
    """Classify each observation's risk level.

    Parameters
    ----------
    df:
        Dataset.
    thresholds:
        Risk thresholds by metric.

    Returns
    -------
    pd.DataFrame
        Dataset with risk_level column.
    """
    if thresholds is None:
        thresholds = RISK_THRESHOLDS

    work = df.copy()
    work["risk_level"] = "normal"
    work["risk_signals"] = ""

    for metric, metric_thresholds in thresholds.items():
        if metric not in work.columns:
            continue

        for level in ["critical", "high", "elevated"]:
            threshold = metric_thresholds[level]

            # For metrics where lower is worse
            if metric in ["was_accepted", "ride_completed", "acceptance_rate", "completion_rate"]:
                mask = work[metric] <= threshold
            else:
                mask = work[metric] >= threshold

            # Update risk level
            level_order = {"normal": 0, "elevated": 1, "high": 2, "critical": 3}
            current_order = work["risk_level"].map(level_order)
            new_order = level_order[level]
            work.loc[mask & (current_order < new_order), "risk_level"] = level

            # Add signal
            work.loc[mask, "risk_signals"] = work.loc[mask, "risk_signals"].apply(
                lambda x: f"{x},{metric}" if x else metric
            )

    return work


# ---------------------------------------------------------------------------
# Risk period identification
# ---------------------------------------------------------------------------

def identify_risk_periods(
    df: pd.DataFrame,
    timestamp_col: str = "request_timestamp",
    city_col: str = "city",
    demand_col: str = "is_high_demand",
) -> pd.DataFrame:
    """Identify time periods with elevated risk.

    Parameters
    ----------
    df:
        Dataset with timestamps.
    timestamp_col:
        Timestamp column.
    city_col:
        City column.
    demand_col:
        High-demand indicator.

    Returns
    -------
    pd.DataFrame
        Risk periods with anomaly counts.
    """
    if timestamp_col not in df.columns:
        return pd.DataFrame()

    # Create time groups (hourly)
    work = df.copy()
    ts = work[timestamp_col]
    if not pd.api.types.is_datetime64_any_dtype(ts):
        ts = pd.to_datetime(ts, errors="coerce", utc=True)
    work["_hour"] = ts.dt.floor("h")

    # Classify risk
    work = classify_risk(work)

    # Aggregate by hour and city
    group_cols = ["_hour"]
    if city_col in work.columns:
        group_cols.append(city_col)

    risk_periods = work.groupby(group_cols).agg(
        total_rides=("ride_id", "count"),
        anomaly_count=("risk_level", lambda x: (x != "normal").sum()),
        elevated_count=("risk_level", lambda x: (x == "elevated").sum()),
        high_count=("risk_level", lambda x: (x == "high").sum()),
        critical_count=("risk_level", lambda x: (x == "critical").sum()),
        avg_demand_supply=("demand_supply_ratio", "mean") if "demand_supply_ratio" in work.columns else ("ride_id", "count"),
        avg_surge=("surge_multiplier", "mean") if "surge_multiplier" in work.columns else ("ride_id", "count"),
        avg_wait=("wait_time_minutes", "mean") if "wait_time_minutes" in work.columns else ("ride_id", "count"),
        avg_cancel=("rider_cancelled", "mean") if "rider_cancelled" in work.columns else ("ride_id", "count"),
    ).reset_index()

    # Calculate anomaly rate
    risk_periods["anomaly_rate"] = risk_periods["anomaly_count"] / risk_periods["total_rides"]

    # Flag high-risk periods (anomaly rate > 30%)
    risk_periods["is_high_risk"] = risk_periods["anomaly_rate"] > 0.30

    return risk_periods


# ---------------------------------------------------------------------------
# City anomaly frequency
# ---------------------------------------------------------------------------

def count_city_anomalies(
    df: pd.DataFrame,
    city_col: str = "city",
) -> pd.DataFrame:
    """Count anomalies by city.

    Parameters
    ----------
    df:
        Dataset.
    city_col:
        City column.

    Returns
    -------
    pd.DataFrame
        Anomaly counts by city.
    """
    work = classify_risk(df)

    result = work.groupby(city_col).agg(
        total_rides=("ride_id", "count"),
        anomaly_count=("risk_level", lambda x: (x != "normal").sum()),
        elevated_count=("risk_level", lambda x: (x == "elevated").sum()),
        high_count=("risk_level", lambda x: (x == "high").sum()),
        critical_count=("risk_level", lambda x: (x == "critical").sum()),
    ).reset_index()

    result["anomaly_rate"] = result["anomaly_count"] / result["total_rides"]

    return result.sort_values("anomaly_rate", ascending=False)
