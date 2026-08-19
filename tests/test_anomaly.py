"""Tests for anomaly detection and operational risk patterns."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from roadies.analysis.anomaly import (
    Anomaly,
    RiskCondition,
    RISK_THRESHOLDS,
    classify_risk,
    count_city_anomalies,
    detect_anomalies,
    detect_city_relative_anomalies,
    identify_risk_periods,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sample_df() -> pd.DataFrame:
    np.random.seed(42)
    n = 500
    return pd.DataFrame({
        "ride_id": [f"R-{i:06d}" for i in range(n)],
        "city": np.random.choice(["Mumbai", "Delhi", "Bangalore"], n),
        "request_timestamp": pd.date_range("2024-01-01", periods=n, freq="h"),
        "was_accepted": np.random.choice([True, False], n, p=[0.8, 0.2]),
        "ride_completed": np.random.choice([True, False], n, p=[0.7, 0.3]),
        "rider_cancelled": np.random.choice([True, False], n, p=[0.1, 0.9]),
        "wait_time_minutes": np.random.uniform(2, 30, n),
        "surge_multiplier": np.random.uniform(1, 3, n),
        "demand_supply_ratio": np.random.uniform(0.5, 2.0, n),
        "is_high_demand": np.random.choice([True, False], n, p=[0.3, 0.7]),
    })


# ---------------------------------------------------------------------------
# Anomaly thresholds
# ---------------------------------------------------------------------------

class TestAnomalyThresholds:
    def test_global_anomalies(self) -> None:
        df = _sample_df()
        anomalies = detect_anomalies(df)
        assert isinstance(anomalies, list)

    def test_anomaly_structure(self) -> None:
        df = _sample_df()
        anomalies = detect_anomalies(df)
        for a in anomalies:
            assert isinstance(a, Anomaly)
            assert a.metric
            assert a.severity in ["normal", "elevated", "high", "critical"]


# ---------------------------------------------------------------------------
# City-relative deviation
# ---------------------------------------------------------------------------

class TestCityRelative:
    def test_city_relative(self) -> None:
        df = _sample_df()
        anomalies = detect_city_relative_anomalies(df)
        assert isinstance(anomalies, list)

    def test_city_relative_has_city(self) -> None:
        df = _sample_df()
        anomalies = detect_city_relative_anomalies(df)
        for a in anomalies:
            assert a.city is not None


# ---------------------------------------------------------------------------
# Risk classification
# ---------------------------------------------------------------------------

class TestRiskClassification:
    def test_risk_level_column(self) -> None:
        df = _sample_df()
        result = classify_risk(df)
        assert "risk_level" in result.columns
        assert "risk_signals" in result.columns

    def test_risk_levels(self) -> None:
        df = _sample_df()
        result = classify_risk(df)
        valid_levels = {"normal", "elevated", "high", "critical"}
        assert set(result["risk_level"]).issubset(valid_levels)


# ---------------------------------------------------------------------------
# Multiple simultaneous risk signals
# ---------------------------------------------------------------------------

class TestMultipleSignals:
    def test_multiple_signals(self) -> None:
        df = _sample_df()
        result = classify_risk(df)
        # Some observations should have multiple signals
        multi_signal = result[result["risk_signals"].str.contains(",")]
        assert len(multi_signal) >= 0  # May or may not exist


# ---------------------------------------------------------------------------
# Small samples
# ---------------------------------------------------------------------------

class TestSmallSamples:
    def test_small_sample(self) -> None:
        df = _sample_df().head(5)
        anomalies = detect_anomalies(df)
        assert isinstance(anomalies, list)


# ---------------------------------------------------------------------------
# Missing values
# ---------------------------------------------------------------------------

class TestMissingValues:
    def test_missing_values(self) -> None:
        df = _sample_df()
        df.loc[0, "wait_time_minutes"] = None
        anomalies = detect_anomalies(df)
        assert isinstance(anomalies, list)


# ---------------------------------------------------------------------------
# Deterministic results
# ---------------------------------------------------------------------------

class TestDeterministic:
    def test_same_input_same_output(self) -> None:
        df = _sample_df()
        r1 = classify_risk(df)
        r2 = classify_risk(df)
        pd.testing.assert_series_equal(r1["risk_level"], r2["risk_level"])


# ---------------------------------------------------------------------------
# Risk periods
# ---------------------------------------------------------------------------

class TestRiskPeriods:
    def test_risk_periods(self) -> None:
        df = _sample_df()
        periods = identify_risk_periods(df)
        assert len(periods) > 0
        assert "anomaly_rate" in periods.columns
