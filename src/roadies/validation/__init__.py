"""SQL/Python metric validation for Roadies-CityRide.

Provides reusable functionality to compare business metrics calculated
in Python with corresponding SQL results to detect computation drift.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from roadies.database import execute_metric_query, get_connection, query


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Default tolerances
DEFAULT_ABSOLUTE_TOLERANCE = 0.01  # 1% for rates
DEFAULT_COUNT_TOLERANCE = 0  # Exact for counts
DEFAULT_FLOAT_TOLERANCE = 0.1  # 0.1 for floating-point values like wait time


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class MetricComparison:
    """Result of comparing a single metric between Python and SQL."""

    metric_name: str
    python_value: float
    sql_value: float
    absolute_difference: float
    relative_difference: float
    tolerance: float
    passed: bool
    category: str = "core"  # "core", "city", "demand"


@dataclass
class ValidationReport:
    """Complete validation report."""

    comparisons: list[MetricComparison] = field(default_factory=list)
    total_metrics: int = 0
    passed_metrics: int = 0
    failed_metrics: int = 0

    def add_comparison(self, comparison: MetricComparison) -> None:
        """Add a comparison to the report."""
        self.comparisons.append(comparison)
        self.total_metrics += 1
        if comparison.passed:
            self.passed_metrics += 1
        else:
            self.failed_metrics += 1

    @property
    def passed(self) -> bool:
        """Whether all comparisons passed."""
        return self.failed_metrics == 0

    def summary(self) -> dict[str, int]:
        """Return summary statistics."""
        return {
            "total": self.total_metrics,
            "passed": self.passed_metrics,
            "failed": self.failed_metrics,
        }


# ---------------------------------------------------------------------------
# Python metric calculation
# ---------------------------------------------------------------------------

def calculate_python_metrics(df: pd.DataFrame) -> dict[str, float]:
    """Calculate core business metrics in Python.

    Parameters
    ----------
    df:
        Ride-level dataset.

    Returns
    -------
    dict[str, float]
        Metric values.
    """
    total = len(df)
    if total == 0:
        return {}

    return {
        "total_rides": float(total),
        "acceptance_rate": float(df["was_accepted"].mean() * 100),
        "completion_rate": float(df["ride_completed"].mean() * 100),
        "rider_cancel_rate": float(df["rider_cancelled"].mean() * 100),
        "driver_cancel_rate": float(df["driver_cancelled"].mean() * 100),
        "avg_wait_time": float(df["wait_time_minutes"].mean()),
        "avg_surge": float(df["surge_multiplier"].mean()),
        "avg_demand_supply_ratio": float(df["demand_supply_ratio"].mean()),
        "high_demand_share": float(df["is_high_demand"].mean() * 100),
    }


def calculate_python_city_metrics(df: pd.DataFrame) -> dict[str, dict[str, float]]:
    """Calculate city-level metrics in Python.

    Parameters
    ----------
    df:
        Ride-level dataset.

    Returns
    -------
    dict[str, dict[str, float]]
        City-level metrics.
    """
    result = {}
    for city, city_df in df.groupby("city"):
        result[city] = {
            "acceptance_rate": float(city_df["was_accepted"].mean() * 100),
            "completion_rate": float(city_df["ride_completed"].mean() * 100),
            "rider_cancel_rate": float(city_df["rider_cancelled"].mean() * 100),
            "avg_wait_time": float(city_df["wait_time_minutes"].mean()),
            "avg_surge": float(city_df["surge_multiplier"].mean()),
        }
    return result


def calculate_python_demand_comparison(df: pd.DataFrame) -> dict[str, dict[str, float]]:
    """Calculate normal vs high demand metrics in Python.

    Parameters
    ----------
    df:
        Ride-level dataset.

    Returns
    -------
    dict[str, dict[str, float]]
        Demand comparison metrics.
    """
    result = {}
    for demand_val, label in [(0, "normal"), (1, "high")]:
        subset = df[df["is_high_demand"] == demand_val]
        if len(subset) > 0:
            result[label] = {
                "acceptance_rate": float(subset["was_accepted"].mean() * 100),
                "rider_cancel_rate": float(subset["rider_cancelled"].mean() * 100),
                "avg_wait_time": float(subset["wait_time_minutes"].mean()),
            }
    return result


# ---------------------------------------------------------------------------
# SQL metric fetching
# ---------------------------------------------------------------------------

def fetch_sql_metrics(db_path: Path | str) -> dict[str, float]:
    """Fetch core metrics from SQL.

    Parameters
    ----------
    db_path:
        Path to SQLite database.

    Returns
    -------
    dict[str, float]
        SQL metric values.
    """
    result = execute_metric_query("core_metrics", db_path)
    row = result.iloc[0]
    return {
        "total_rides": float(row["total_rides"]),
        "acceptance_rate": float(row["acceptance_rate"]),
        "completion_rate": float(row["completion_rate"]),
        "rider_cancel_rate": float(row["rider_cancel_rate"]),
        "driver_cancel_rate": float(row["driver_cancel_rate"]),
        "avg_wait_time": float(row["avg_wait_time"]),
        "avg_surge": float(row["avg_surge"]),
        "avg_demand_supply_ratio": float(row["avg_demand_supply_ratio"]),
        "high_demand_share": float(row["high_demand_share"]),
    }


def fetch_sql_city_metrics(db_path: Path | str) -> dict[str, dict[str, float]]:
    """Fetch city-level metrics from SQL.

    Parameters
    ----------
    db_path:
        Path to SQLite database.

    Returns
    -------
    dict[str, dict[str, float]]
        City-level SQL metrics.
    """
    result = execute_metric_query("city_metrics", db_path)
    city_metrics = {}
    for _, row in result.iterrows():
        city_metrics[row["city"]] = {
            "acceptance_rate": float(row["acceptance_rate"]),
            "completion_rate": float(row["completion_rate"]),
            "rider_cancel_rate": float(row["rider_cancel_rate"]),
            "avg_wait_time": float(row["avg_wait_time"]),
            "avg_surge": float(row["avg_surge"]),
        }
    return city_metrics


def fetch_sql_demand_comparison(db_path: Path | str) -> dict[str, dict[str, float]]:
    """Fetch demand comparison metrics from SQL.

    Parameters
    ----------
    db_path:
        Path to SQLite database.

    Returns
    -------
    dict[str, dict[str, float]]
        Demand comparison SQL metrics.
    """
    result = execute_metric_query("demand_comparison", db_path)
    demand_metrics = {}
    for _, row in result.iterrows():
        demand_metrics[row["demand_period"]] = {
            "acceptance_rate": float(row["acceptance_rate"]),
            "rider_cancel_rate": float(row["rider_cancel_rate"]),
            "avg_wait_time": float(row["avg_wait_time"]),
        }
    return demand_metrics


# ---------------------------------------------------------------------------
# Comparison functions
# ---------------------------------------------------------------------------

def compare_metrics(
    python_value: float,
    sql_value: float,
    metric_name: str,
    absolute_tolerance: float = DEFAULT_ABSOLUTE_TOLERANCE,
    category: str = "core",
) -> MetricComparison:
    """Compare a single Python and SQL metric value.

    Parameters
    ----------
    python_value:
        Python-calculated value.
    sql_value:
        SQL-calculated value.
    metric_name:
        Name of the metric.
    absolute_tolerance:
        Allowed absolute difference.
    category:
        Metric category.

    Returns
    -------
    MetricComparison
        Comparison result.
    """
    abs_diff = abs(python_value - sql_value)
    rel_diff = abs_diff / abs(python_value) if python_value != 0 else 0
    passed = abs_diff <= absolute_tolerance

    return MetricComparison(
        metric_name=metric_name,
        python_value=python_value,
        sql_value=sql_value,
        absolute_difference=abs_diff,
        relative_difference=rel_diff,
        tolerance=absolute_tolerance,
        passed=passed,
        category=category,
    )


# ---------------------------------------------------------------------------
# Main validation function
# ---------------------------------------------------------------------------

def validate_sql_against_python(
    df: pd.DataFrame,
    db_path: Path | str,
    absolute_tolerance: float = DEFAULT_ABSOLUTE_TOLERANCE,
    count_tolerance: float = DEFAULT_COUNT_TOLERANCE,
) -> ValidationReport:
    """Validate SQL metrics against Python calculations.

    Parameters
    ----------
    df:
        Python dataset for metric calculation.
    db_path:
        Path to SQLite database.
    absolute_tolerance:
        Tolerance for rate/percentage metrics.
    count_tolerance:
        Tolerance for count metrics.

    Returns
    -------
    ValidationReport
        Validation results.
    """
    report = ValidationReport()

    # Calculate Python metrics
    python_metrics = calculate_python_metrics(df)
    sql_metrics = fetch_sql_metrics(db_path)

    # Compare core metrics
    for metric in python_metrics:
        if metric in sql_metrics:
            tolerance = count_tolerance if metric == "total_rides" else absolute_tolerance
            comparison = compare_metrics(
                python_metrics[metric],
                sql_metrics[metric],
                metric,
                tolerance,
                category="core",
            )
            report.add_comparison(comparison)

    # Compare city-level metrics
    python_city = calculate_python_city_metrics(df)
    sql_city = fetch_sql_city_metrics(db_path)

    for city in python_city:
        if city in sql_city:
            for metric in python_city[city]:
                if metric in sql_city[city]:
                    comparison = compare_metrics(
                        python_city[city][metric],
                        sql_city[city][metric],
                        f"{city}_{metric}",
                        absolute_tolerance,
                        category="city",
                    )
                    report.add_comparison(comparison)

    # Compare demand comparison metrics
    python_demand = calculate_python_demand_comparison(df)
    sql_demand = fetch_sql_demand_comparison(db_path)

    for period in python_demand:
        if period in sql_demand:
            for metric in python_demand[period]:
                if metric in sql_demand[period]:
                    comparison = compare_metrics(
                        python_demand[period][metric],
                        sql_demand[period][metric],
                        f"{period}_{metric}",
                        absolute_tolerance,
                        category="demand",
                    )
                    report.add_comparison(comparison)

    return report
