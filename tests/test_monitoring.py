"""Tests for monitoring and pipeline execution."""

from __future__ import annotations

import os
import numpy as np
import pandas as pd
import pytest

from roadies.monitoring import (
    Alert,
    AlertResult,
    MonitoringThresholds,
    Severity,
    evaluate_alerts,
    run_pipeline,
)

HAS_REAL_DATASET = os.path.exists("data/raw/rides.csv")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sample_df() -> pd.DataFrame:
    np.random.seed(42)
    n = 500
    return pd.DataFrame({
        "city": np.random.choice(["Mumbai", "Delhi", "Bangalore"], n),
        "was_accepted": np.random.choice([True, False], n, p=[0.8, 0.2]),
        "rider_cancelled": np.random.choice([True, False], n, p=[0.1, 0.9]),
        "was_completed": np.random.choice([True, False], n, p=[0.75, 0.25]),
        "wait_time_minutes": np.random.uniform(2, 30, n),
        "surge_multiplier": np.random.uniform(1, 3, n),
        "is_high_demand": np.random.choice([True, False], n, p=[0.3, 0.7]),
    })


def _high_cancel_df() -> pd.DataFrame:
    """DF with high cancellation in high-demand."""
    df = _sample_df()
    # Force high cancel in high demand
    mask = df["is_high_demand"]
    df.loc[mask, "rider_cancelled"] = True
    return df


# ---------------------------------------------------------------------------
# Pipeline execution
# ---------------------------------------------------------------------------

class TestPipeline:
    def test_run_pipeline_returns_dict(self) -> None:
        result = run_pipeline("data/raw/rides.csv")
        assert isinstance(result, dict)

    def test_pipeline_has_keys(self) -> None:
        if not HAS_REAL_DATASET:
            pytest.skip("Real dataset not available")
        result = run_pipeline("data/raw/rides.csv")
        assert "dataframe" in result
        assert "kpis" in result
        assert "alerts" in result

    def test_pipeline_missing_file(self) -> None:
        result = run_pipeline("/nonexistent/path.csv")
        assert "error" in result

    def test_pipeline_with_synthetic_df(self) -> None:
        df = _sample_df()
        df.to_csv("/tmp/test_pipeline.csv", index=False)
        result = run_pipeline("/tmp/test_pipeline.csv")
        assert "dataframe" in result
        assert "alerts" in result
        assert isinstance(result["alerts"], AlertResult)


# ---------------------------------------------------------------------------
# Alert threshold logic
# ---------------------------------------------------------------------------

class TestAlertThresholds:
    def test_evaluate_alerts_returns_result(self) -> None:
        df = _sample_df()
        result = evaluate_alerts(df)
        assert isinstance(result, AlertResult)

    def test_alerts_have_required_fields(self) -> None:
        df = _sample_df()
        result = evaluate_alerts(df)
        for alert in result.alerts:
            assert isinstance(alert, Alert)
            assert alert.name
            assert isinstance(alert.severity, Severity)
            assert alert.metric
            assert isinstance(alert.threshold, (int, float))


# ---------------------------------------------------------------------------
# Severity mapping
# ---------------------------------------------------------------------------

class TestSeverity:
    def test_severity_values(self) -> None:
        assert Severity.INFO.value == "info"
        assert Severity.WARNING.value == "warning"
        assert Severity.HIGH.value == "high"
        assert Severity.CRITICAL.value == "critical"


# ---------------------------------------------------------------------------
# No-alert conditions
# ---------------------------------------------------------------------------

class TestNoAlert:
    def test_low_cancel_no_alert(self) -> None:
        df = _sample_df()
        # Ensure cancel rate is low
        df["rider_cancelled"] = False
        df.loc[df["is_high_demand"], "rider_cancelled"] = False
        result = evaluate_alerts(df)
        cancel_alerts = [a for a in result.alerts if "rider_cancel" in a.name]
        assert all(not a.triggered for a in cancel_alerts)


# ---------------------------------------------------------------------------
# Triggered-alert conditions
# ---------------------------------------------------------------------------

class TestTriggeredAlert:
    def test_high_cancel_triggers(self) -> None:
        df = _high_cancel_df()
        result = evaluate_alerts(df)
        cancel_alerts = [a for a in result.alerts if "rider_cancel" in a.name]
        assert any(a.triggered for a in cancel_alerts)


# ---------------------------------------------------------------------------
# City-level alerts
# ---------------------------------------------------------------------------

class TestCityAlerts:
    def test_city_alerts_exist(self) -> None:
        df = _sample_df()
        result = evaluate_alerts(df)
        city_alerts = [a for a in result.alerts if a.city is not None]
        assert len(city_alerts) > 0


# ---------------------------------------------------------------------------
# High-demand alerts
# ---------------------------------------------------------------------------

class TestHighDemandAlerts:
    def test_high_demand_alerts_exist(self) -> None:
        df = _sample_df()
        result = evaluate_alerts(df)
        hd_alerts = [a for a in result.alerts if a.period == "high_demand"]
        assert len(hd_alerts) > 0


# ---------------------------------------------------------------------------
# Minimum sample size
# ---------------------------------------------------------------------------

class TestMinSampleSize:
    def test_small_sample_no_alerts(self) -> None:
        df = pd.DataFrame({
            "city": ["Mumbai", "Delhi"],
            "was_accepted": [True, False],
            "rider_cancelled": [True, False],
            "wait_time_minutes": [5, 10],
            "surge_multiplier": [1.2, 2.5],
            "is_high_demand": [True, False],
        })
        result = evaluate_alerts(df, MonitoringThresholds(min_sample_size=30))
        assert result.total_triggered == 0


# ---------------------------------------------------------------------------
# Configurable thresholds
# ---------------------------------------------------------------------------

class TestConfigurableThresholds:
    def test_custom_thresholds(self) -> None:
        df = _sample_df()
        t = MonitoringThresholds(rider_cancel_high=5.0)
        result = evaluate_alerts(df, t)
        cancel_alerts = [a for a in result.alerts if a.name == "high_demand_rider_cancel"]
        assert len(cancel_alerts) == 1
        assert cancel_alerts[0].threshold == 5.0


# ---------------------------------------------------------------------------
# Deterministic execution
# ---------------------------------------------------------------------------

class TestDeterministic:
    def test_same_input_same_output(self) -> None:
        df = _sample_df()
        r1 = evaluate_alerts(df)
        r2 = evaluate_alerts(df)
        assert r1.total_triggered == r2.total_triggered


# ---------------------------------------------------------------------------
# Generated dataset integration
# ---------------------------------------------------------------------------

class TestIntegration:
    def test_full_workflow_with_real_data(self) -> None:
        if not HAS_REAL_DATASET:
            pytest.skip("Real dataset not available")
        result = run_pipeline("data/raw/rides.csv")
        assert "dataframe" in result
        assert "kpis" in result
        assert "alerts" in result
        alert_result = result["alerts"]
        assert isinstance(alert_result, AlertResult)

    def test_full_workflow_with_synthetic_data(self) -> None:
        df = _sample_df()
        df.to_csv("/tmp/test_integration.csv", index=False)
        result = run_pipeline("/tmp/test_integration.csv")
        assert "dataframe" in result
        assert "alerts" in result
        alert_result = result["alerts"]
        assert isinstance(alert_result, AlertResult)
