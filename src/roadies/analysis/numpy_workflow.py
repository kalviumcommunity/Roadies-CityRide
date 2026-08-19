"""NumPy vectorised computation workflow for Roadies-CityRide.

Provides reusable vectorised numerical operations for performance-critical
feature calculations and analytical workflows.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class BenchmarkResult:
    """Benchmark comparison result."""

    operation: str
    dataset_size: int
    baseline_time: float
    vectorised_time: float
    speedup: float


# ---------------------------------------------------------------------------
# Vectorised computations
# ---------------------------------------------------------------------------

def vectorised_demand_supply_ratio(
    demand: np.ndarray,
    supply: np.ndarray,
) -> np.ndarray:
    """Compute demand/supply ratio using vectorised NumPy operations.

    Parameters
    ----------
    demand:
        Array of demand values.
    supply:
        Array of supply values.

    Returns
    -------
    np.ndarray
        Demand/supply ratio with safe division.
    """
    demand = np.asarray(demand, dtype=np.float64)
    supply = np.asarray(supply, dtype=np.float64)

    # Handle zero denominators
    safe_supply = np.where(supply == 0, np.nan, supply)
    result = np.where(np.isnan(safe_supply), np.nan, demand / safe_supply)

    return result


def baseline_demand_supply_ratio(
    demand: pd.Series,
    supply: pd.Series,
) -> pd.Series:
    """Baseline Pandas implementation for comparison."""
    return demand / supply.replace(0, np.nan)


def vectorised_percentage_change(
    old_values: np.ndarray,
    new_values: np.ndarray,
) -> np.ndarray:
    """Compute percentage change using vectorised operations.

    Parameters
    ----------
    old_values:
        Original values.
    new_values:
        New values.

    Returns
    -------
    np.ndarray
        Percentage change with safe division.
    """
    old_values = np.asarray(old_values, dtype=np.float64)
    new_values = np.asarray(new_values, dtype=np.float64)

    safe_old = np.where(old_values == 0, np.nan, old_values)
    result = np.where(np.isnan(safe_old), np.nan, (new_values - old_values) / safe_old)

    return result


def baseline_percentage_change(
    old_values: pd.Series,
    new_values: pd.Series,
) -> pd.Series:
    """Baseline Pandas implementation."""
    return (new_values - old_values) / old_values.replace(0, np.nan)


def vectorised_deviation_from_baseline(
    values: np.ndarray,
    baseline: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute absolute and relative deviation from baseline.

    Parameters
    ----------
    values:
        Observed values.
    baseline:
        Baseline values.

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        Absolute deviation and relative deviation.
    """
    values = np.asarray(values, dtype=np.float64)
    baseline = np.asarray(baseline, dtype=np.float64)

    abs_dev = values - baseline
    safe_baseline = np.where(baseline == 0, np.nan, baseline)
    rel_dev = np.where(np.isnan(safe_baseline), np.nan, abs_dev / safe_baseline)

    return abs_dev, rel_dev


def vectorised_risk_classification(
    values: np.ndarray,
    elevated_threshold: float,
    high_threshold: float,
    critical_threshold: float,
    higher_is_worse: bool = True,
) -> np.ndarray:
    """Classify risk levels using vectorised operations.

    Parameters
    ----------
    values:
        Metric values.
    elevated_threshold:
        Threshold for elevated risk.
    high_threshold:
        Threshold for high risk.
    critical_threshold:
        Threshold for critical risk.
    higher_is_worse:
        If True, higher values are worse.

    Returns
    -------
    np.ndarray
        Risk levels: 0=normal, 1=elevated, 2=high, 3=critical.
    """
    values = np.asarray(values, dtype=np.float64)

    if higher_is_worse:
        risk = np.where(values >= critical_threshold, 3,
                np.where(values >= high_threshold, 2,
                np.where(values >= elevated_threshold, 1, 0)))
    else:
        risk = np.where(values <= critical_threshold, 3,
                np.where(values <= high_threshold, 2,
                np.where(values <= elevated_threshold, 1, 0)))

    return risk.astype(np.int32)


def vectorised_zscore(
    values: np.ndarray,
    mean: float | None = None,
    std: float | None = None,
) -> np.ndarray:
    """Compute z-scores using vectorised operations.

    Parameters
    ----------
    values:
        Input values.
    mean:
        Optional pre-computed mean.
    std:
        Optional pre-computed standard deviation.

    Returns
    -------
    np.ndarray
        Z-scores.
    """
    values = np.asarray(values, dtype=np.float64)

    if mean is None:
        mean = np.nanmean(values)
    if std is None:
        std = np.nanstd(values)

    if std == 0:
        return np.zeros_like(values)

    return (values - mean) / std


def vectorised_normalise(
    values: np.ndarray,
    min_val: float | None = None,
    max_val: float | None = None,
) -> np.ndarray:
    """Normalise values to [0, 1] range using vectorised operations.

    Parameters
    ----------
    values:
        Input values.
    min_val:
        Optional pre-computed minimum.
    max_val:
        Optional pre-computed maximum.

    Returns
    -------
    np.ndarray
        Normalised values.
    """
    values = np.asarray(values, dtype=np.float64)

    if min_val is None:
        min_val = np.nanmin(values)
    if max_val is None:
        max_val = np.nanmax(values)

    range_val = max_val - min_val
    if range_val == 0:
        return np.zeros_like(values)

    return (values - min_val) / range_val


# ---------------------------------------------------------------------------
# Benchmark
# ---------------------------------------------------------------------------

def benchmark_operations(
    n_rows: int = 100_000,
    n_iterations: int = 10,
) -> list[BenchmarkResult]:
    """Benchmark vectorised vs baseline implementations.

    Parameters
    ----------
    n_rows:
        Dataset size for benchmark.
    n_iterations:
        Number of iterations for averaging.

    Returns
    -------
    list[BenchmarkResult]
        Benchmark results.
    """
    np.random.seed(42)
    demand = np.random.uniform(100, 1000, n_rows)
    supply = np.random.uniform(50, 500, n_rows)
    old_vals = np.random.uniform(10, 100, n_rows)
    new_vals = old_vals * np.random.uniform(0.8, 1.2, n_rows)

    results = []

    # Benchmark demand/supply ratio
    baseline_times = []
    vectorised_times = []

    for _ in range(n_iterations):
        # Baseline
        start = time.perf_counter()
        df = pd.DataFrame({"demand": demand, "supply": supply})
        _ = df["demand"] / df["supply"].replace(0, np.nan)
        baseline_times.append(time.perf_counter() - start)

        # Vectorised
        start = time.perf_counter()
        _ = vectorised_demand_supply_ratio(demand, supply)
        vectorised_times.append(time.perf_counter() - start)

    avg_baseline = np.mean(baseline_times)
    avg_vectorised = np.mean(vectorised_times)
    speedup = avg_baseline / avg_vectorised if avg_vectorised > 0 else 0

    results.append(BenchmarkResult(
        operation="demand_supply_ratio",
        dataset_size=n_rows,
        baseline_time=avg_baseline,
        vectorised_time=avg_vectorised,
        speedup=speedup,
    ))

    # Benchmark percentage change
    baseline_times = []
    vectorised_times = []

    for _ in range(n_iterations):
        # Baseline
        start = time.perf_counter()
        df = pd.DataFrame({"old": old_vals, "new": new_vals})
        _ = (df["new"] - df["old"]) / df["old"].replace(0, np.nan)
        baseline_times.append(time.perf_counter() - start)

        # Vectorised
        start = time.perf_counter()
        _ = vectorised_percentage_change(old_vals, new_vals)
        vectorised_times.append(time.perf_counter() - start)

    avg_baseline = np.mean(baseline_times)
    avg_vectorised = np.mean(vectorised_times)
    speedup = avg_baseline / avg_vectorised if avg_vectorised > 0 else 0

    results.append(BenchmarkResult(
        operation="percentage_change",
        dataset_size=n_rows,
        baseline_time=avg_baseline,
        vectorised_time=avg_vectorised,
        speedup=speedup,
    ))

    return results
