"""Tests for NumPy vectorised computation workflow."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from roadies.analysis.numpy_workflow import (
    BenchmarkResult,
    baseline_demand_supply_ratio,
    baseline_percentage_change,
    benchmark_operations,
    vectorised_demand_supply_ratio,
    vectorised_deviation_from_baseline,
    vectorised_normalise,
    vectorised_percentage_change,
    vectorised_risk_classification,
    vectorised_zscore,
)


# ---------------------------------------------------------------------------
# Numerical correctness
# ---------------------------------------------------------------------------

class TestNumericalCorrectness:
    def test_demand_supply_basic(self) -> None:
        demand = np.array([100, 200, 300])
        supply = np.array([50, 100, 150])
        result = vectorised_demand_supply_ratio(demand, supply)
        expected = np.array([2.0, 2.0, 2.0])
        np.testing.assert_array_almost_equal(result, expected)

    def test_percentage_change_basic(self) -> None:
        old = np.array([100, 200, 300])
        new = np.array([110, 180, 330])
        result = vectorised_percentage_change(old, new)
        expected = np.array([0.1, -0.1, 0.1])
        np.testing.assert_array_almost_equal(result, expected)


# ---------------------------------------------------------------------------
# Zero-division behaviour
# ---------------------------------------------------------------------------

class TestZeroDivision:
    def test_demand_supply_zero_supply(self) -> None:
        demand = np.array([100, 200])
        supply = np.array([0, 100])
        result = vectorised_demand_supply_ratio(demand, supply)
        assert np.isnan(result[0])
        assert result[1] == 2.0

    def test_percentage_change_zero_old(self) -> None:
        old = np.array([0, 100])
        new = np.array([10, 110])
        result = vectorised_percentage_change(old, new)
        assert np.isnan(result[0])
        assert result[1] == 0.1


# ---------------------------------------------------------------------------
# Missing-value handling
# ---------------------------------------------------------------------------

class TestMissingValues:
    def test_nan_handling(self) -> None:
        demand = np.array([100, np.nan, 300])
        supply = np.array([50, 100, 150])
        result = vectorised_demand_supply_ratio(demand, supply)
        assert np.isnan(result[1])
        assert result[0] == 2.0
        assert result[2] == 2.0


# ---------------------------------------------------------------------------
# Floating-point consistency
# ---------------------------------------------------------------------------

class TestFloatingPoint:
    def test_precision(self) -> None:
        demand = np.array([1.0])
        supply = np.array([3.0])
        result = vectorised_demand_supply_ratio(demand, supply)
        assert abs(result[0] - 0.3333333333333333) < 1e-10


# ---------------------------------------------------------------------------
# Vectorised vs baseline equivalence
# ---------------------------------------------------------------------------

class TestEquivalence:
    def test_demand_supply_equivalence(self) -> None:
        np.random.seed(42)
        demand = np.random.uniform(100, 1000, 100)
        supply = np.random.uniform(50, 500, 100)

        vec_result = vectorised_demand_supply_ratio(demand, supply)
        base_result = baseline_demand_supply_ratio(
            pd.Series(demand), pd.Series(supply)
        ).values

        np.testing.assert_array_almost_equal(vec_result, base_result)

    def test_percentage_change_equivalence(self) -> None:
        np.random.seed(42)
        old = np.random.uniform(10, 100, 100)
        new = old * np.random.uniform(0.8, 1.2, 100)

        vec_result = vectorised_percentage_change(old, new)
        base_result = baseline_percentage_change(
            pd.Series(old), pd.Series(new)
        ).values

        np.testing.assert_array_almost_equal(vec_result, base_result)


# ---------------------------------------------------------------------------
# Risk classification
# ---------------------------------------------------------------------------

class TestRiskClassification:
    def test_higher_is_worse(self) -> None:
        values = np.array([1.0, 1.6, 2.1, 2.6])
        result = vectorised_risk_classification(values, 1.5, 2.0, 2.5)
        expected = np.array([0, 1, 2, 3])
        np.testing.assert_array_equal(result, expected)

    def test_lower_is_worse(self) -> None:
        values = np.array([0.9, 0.74, 0.69, 0.64])
        result = vectorised_risk_classification(values, 0.75, 0.70, 0.65, higher_is_worse=False)
        expected = np.array([0, 1, 2, 3])
        np.testing.assert_array_equal(result, expected)


# ---------------------------------------------------------------------------
# Z-score and normalisation
# ---------------------------------------------------------------------------

class TestZscore:
    def test_zscore(self) -> None:
        values = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = vectorised_zscore(values)
        assert abs(np.nanmean(result)) < 1e-10
        assert abs(np.nanstd(result) - 1.0) < 1e-10


class TestNormalise:
    def test_normalise(self) -> None:
        values = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
        result = vectorised_normalise(values)
        assert result[0] == 0.0
        assert result[-1] == 1.0


# ---------------------------------------------------------------------------
# Benchmark
# ---------------------------------------------------------------------------

class TestBenchmark:
    def test_benchmark(self) -> None:
        results = benchmark_operations(n_rows=10_000, n_iterations=2)
        assert len(results) == 2
        for r in results:
            assert isinstance(r, BenchmarkResult)
            assert r.speedup > 0


# ---------------------------------------------------------------------------
# Generated dataset integration
# ---------------------------------------------------------------------------

class TestIntegration:
    def test_with_dataframe(self) -> None:
        np.random.seed(42)
        n = 500
        df = pd.DataFrame({
            "demand": np.random.uniform(100, 1000, n),
            "supply": np.random.uniform(50, 500, n),
        })
        result = vectorised_demand_supply_ratio(
            df["demand"].values, df["supply"].values
        )
        assert len(result) == n
        assert not np.all(np.isnan(result))
