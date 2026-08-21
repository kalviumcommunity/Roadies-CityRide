"""Alert monitoring and automated pipeline execution for Roadies-CityRide."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

import pandas as pd

from roadies.features.acceptance import engineer_acceptance_features
from roadies.features.cancellation import engineer_cancellation_features
from roadies.features.demand_period import classify_high_demand
from roadies.features.demand_supply import engineer_demand_supply_features
from roadies.features.experience import engineer_experience_features
from roadies.features.surge import engineer_surge_features
from roadies.ingestion.loaders import load_csv
from roadies.visualization.kpis import calculate_kpis

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Severity levels
# ---------------------------------------------------------------------------

class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    HIGH = "high"
    CRITICAL = "critical"


# ---------------------------------------------------------------------------
# Alert data structures
# ---------------------------------------------------------------------------

@dataclass
class Alert:
    name: str
    severity: Severity
    metric: str
    observed_value: float
    threshold: float
    comparison: str
    city: str | None = None
    period: str | None = None
    message: str = ""
    triggered: bool = False


@dataclass
class AlertResult:
    alerts: list[Alert] = field(default_factory=list)
    total_triggered: int = 0
    total_evaluated: int = 0

    def triggered_alerts(self) -> list[Alert]:
        return [a for a in self.alerts if a.triggered]


# ---------------------------------------------------------------------------
# Default thresholds
# ---------------------------------------------------------------------------

@dataclass
class MonitoringThresholds:
    rider_cancel_high: float = 20.0
    rider_cancel_normal: float = 15.0
    acceptance_low: float = 70.0
    acceptance_deterioration: float = -10.0
    wait_time_high: float = 15.0
    wait_time_deterioration: float = 5.0
    surge_high: float = 2.0
    surge_deterioration: float = 0.5
    min_sample_size: int = 30


# ---------------------------------------------------------------------------
# Pipeline execution
# ---------------------------------------------------------------------------

def run_pipeline(csv_path: str | Path = "data/raw/rides.csv") -> dict:
    """Run the full analytical pipeline.

    Returns
    -------
    dict
        Pipeline results with dataframe, KPIs, alerts, etc.
    """
    results = {}
    p = Path(csv_path)

    # Stage 1: Load
    logger.info("Stage 1: Loading dataset")
    if not p.exists():
        logger.warning("Dataset not found at %s", p)
        return {"error": "Dataset not found", "dataframe": pd.DataFrame()}
    df = load_csv(p)
    results["rows_loaded"] = len(df)
    logger.info("Loaded %d rows", len(df))

    # Stage 2: Feature engineering
    logger.info("Stage 2: Feature engineering")
    for name, func in [
        ("demand_supply", engineer_demand_supply_features),
        ("surge", engineer_surge_features),
        ("acceptance", engineer_acceptance_features),
        ("cancellation", engineer_cancellation_features),
        ("experience", engineer_experience_features),
        ("demand_period", classify_high_demand),
    ]:
        try:
            df, _ = func(df)
        except (KeyError, ValueError) as exc:
            logger.warning("Skipping %s: %s", name, exc)
    results["dataframe"] = df

    # Stage 3: KPI calculation
    logger.info("Stage 3: KPI calculation")
    kpis = calculate_kpis(df)
    results["kpis"] = kpis

    # Stage 4: Alert evaluation
    logger.info("Stage 4: Alert evaluation")
    alert_result = evaluate_alerts(df)
    results["alerts"] = alert_result
    results["triggered_count"] = alert_result.total_triggered

    logger.info("Pipeline complete. %d alerts triggered.", alert_result.total_triggered)
    return results


# ---------------------------------------------------------------------------
# Alert evaluation
# ---------------------------------------------------------------------------

def evaluate_alerts(
    df: pd.DataFrame,
    thresholds: MonitoringThresholds | None = None,
) -> AlertResult:
    """Evaluate alert rules against the dataset.

    Parameters
    ----------
    df:
        Ride dataset with features.
    thresholds:
        Alert thresholds.

    Returns
    -------
    AlertResult
        Structured alert results.
    """
    if thresholds is None:
        thresholds = MonitoringThresholds()

    result = AlertResult()

    if df.empty:
        return result

    normal = df[~df["is_high_demand"]] if "is_high_demand" in df.columns else df
    high = df[df["is_high_demand"]] if "is_high_demand" in df.columns else df

    # Global high-demand alerts
    if len(high) >= thresholds.min_sample_size:
        _check_rider_cancel(high, thresholds, result)
        _check_acceptance(high, normal, thresholds, result)
        _check_wait_time(high, normal, thresholds, result)
        _check_surge(high, thresholds, result)

    # Per-city alerts
    if "city" in df.columns:
        for city_name, city_df in df.groupby("city"):
            city_high = city_df[city_df["is_high_demand"]] if "is_high_demand" in city_df.columns else city_df
            city_normal = city_df[~city_df["is_high_demand"]] if "is_high_demand" in city_df.columns else city_df

            if len(city_high) >= thresholds.min_sample_size:
                _check_city_rider_cancel(city_name, city_high, thresholds, result)
                _check_city_acceptance(city_name, city_high, city_normal, thresholds, result)
                _check_city_wait_time(city_name, city_high, city_normal, thresholds, result)
                _check_city_surge(city_name, city_high, thresholds, result)

    result.total_evaluated = len(result.alerts)
    result.total_triggered = len(result.triggered_alerts())
    return result


def _check_rider_cancel(high: pd.DataFrame, t: MonitoringThresholds, r: AlertResult) -> None:
    rate = high["rider_cancelled"].mean() * 100
    triggered = rate > t.rider_cancel_high
    r.alerts.append(Alert(
        name="high_demand_rider_cancel",
        severity=Severity.HIGH if triggered else Severity.INFO,
        metric="rider_cancel_rate",
        observed_value=rate,
        threshold=t.rider_cancel_high,
        comparison="high demand vs threshold",
        period="high_demand",
        message=f"High-demand rider cancel rate {rate:.1f}% {'exceeds' if triggered else 'within'} threshold {t.rider_cancel_high}%",
        triggered=triggered,
    ))


def _check_acceptance(high: pd.DataFrame, normal: pd.DataFrame, t: MonitoringThresholds, r: AlertResult) -> None:
    high_rate = high["was_accepted"].mean() * 100
    normal_rate = normal["was_accepted"].mean() * 100
    deterioration = high_rate - normal_rate

    triggered_abs = high_rate < t.acceptance_low
    triggered_rel = deterioration < t.acceptance_deterioration

    r.alerts.append(Alert(
        name="high_demand_acceptance_low",
        severity=Severity.CRITICAL if triggered_abs else Severity.INFO,
        metric="acceptance_rate",
        observed_value=high_rate,
        threshold=t.acceptance_low,
        comparison="high demand vs threshold",
        period="high_demand",
        message=f"High-demand acceptance {high_rate:.1f}% {'below' if triggered_abs else 'above'} threshold {t.acceptance_low}%",
        triggered=triggered_abs,
    ))

    r.alerts.append(Alert(
        name="high_demand_acceptance_deterioration",
        severity=Severity.HIGH if triggered_rel else Severity.INFO,
        metric="acceptance_deterioration",
        observed_value=deterioration,
        threshold=t.acceptance_deterioration,
        comparison=f"high ({high_rate:.1f}%) vs normal ({normal_rate:.1f}%)",
        period="high_demand",
        message=f"Acceptance deteriorated {deterioration:.1f}pp {'beyond' if triggered_rel else 'within'} threshold {t.acceptance_deterioration}pp",
        triggered=triggered_rel,
    ))


def _check_wait_time(high: pd.DataFrame, normal: pd.DataFrame, t: MonitoringThresholds, r: AlertResult) -> None:
    high_wait = high["wait_time_minutes"].mean()
    normal_wait = normal["wait_time_minutes"].mean()
    deterioration = high_wait - normal_wait

    triggered_abs = high_wait > t.wait_time_high
    triggered_rel = deterioration > t.wait_time_deterioration

    r.alerts.append(Alert(
        name="high_demand_wait_time_high",
        severity=Severity.HIGH if triggered_abs else Severity.INFO,
        metric="avg_wait_time",
        observed_value=high_wait,
        threshold=t.wait_time_high,
        comparison="high demand vs threshold",
        period="high_demand",
        message=f"High-demand wait time {high_wait:.1f}min {'exceeds' if triggered_abs else 'within'} threshold {t.wait_time_high}min",
        triggered=triggered_abs,
    ))

    r.alerts.append(Alert(
        name="high_demand_wait_time_deterioration",
        severity=Severity.WARNING if triggered_rel else Severity.INFO,
        metric="wait_time_deterioration",
        observed_value=deterioration,
        threshold=t.wait_time_deterioration,
        comparison=f"high ({high_wait:.1f}) vs normal ({normal_wait:.1f})",
        period="high_demand",
        message=f"Wait time increased {deterioration:.1f}min {'beyond' if triggered_rel else 'within'} threshold {t.wait_time_deterioration}min",
        triggered=triggered_rel,
    ))


def _check_surge(high: pd.DataFrame, t: MonitoringThresholds, r: AlertResult) -> None:
    surge = high["surge_multiplier"].mean()
    triggered = surge > t.surge_high

    r.alerts.append(Alert(
        name="high_demand_surge_high",
        severity=Severity.HIGH if triggered else Severity.INFO,
        metric="avg_surge",
        observed_value=surge,
        threshold=t.surge_high,
        comparison="high demand vs threshold",
        period="high_demand",
        message=f"High-demand surge {surge:.2f}x {'exceeds' if triggered else 'within'} threshold {t.surge_high}x",
        triggered=triggered,
    ))


def _check_city_rider_cancel(city: str, high: pd.DataFrame, t: MonitoringThresholds, r: AlertResult) -> None:
    rate = high["rider_cancelled"].mean() * 100
    triggered = rate > t.rider_cancel_high
    r.alerts.append(Alert(
        name=f"city_{city}_rider_cancel",
        severity=Severity.HIGH if triggered else Severity.INFO,
        metric="rider_cancel_rate",
        observed_value=rate,
        threshold=t.rider_cancel_high,
        comparison=f"{city} high demand vs threshold",
        city=city,
        period="high_demand",
        message=f"{city} high-demand rider cancel {rate:.1f}% {'exceeds' if triggered else 'within'} {t.rider_cancel_high}%",
        triggered=triggered,
    ))


def _check_city_acceptance(city: str, high: pd.DataFrame, normal: pd.DataFrame, t: MonitoringThresholds, r: AlertResult) -> None:
    high_rate = high["was_accepted"].mean() * 100
    deterioration = high_rate - (normal["was_accepted"].mean() * 100 if len(normal) > 0 else high_rate)
    triggered = high_rate < t.acceptance_low or deterioration < t.acceptance_deterioration

    r.alerts.append(Alert(
        name=f"city_{city}_acceptance",
        severity=Severity.HIGH if triggered else Severity.INFO,
        metric="acceptance_rate",
        observed_value=high_rate,
        threshold=t.acceptance_low,
        comparison=f"{city} high demand",
        city=city,
        period="high_demand",
        message=f"{city} acceptance {high_rate:.1f}% {'below threshold' if triggered else 'acceptable'}",
        triggered=triggered,
    ))


def _check_city_wait_time(city: str, high: pd.DataFrame, normal: pd.DataFrame, t: MonitoringThresholds, r: AlertResult) -> None:
    high_wait = high["wait_time_minutes"].mean()
    triggered = high_wait > t.wait_time_high

    r.alerts.append(Alert(
        name=f"city_{city}_wait_time",
        severity=Severity.HIGH if triggered else Severity.INFO,
        metric="avg_wait_time",
        observed_value=high_wait,
        threshold=t.wait_time_high,
        comparison=f"{city} high demand",
        city=city,
        period="high_demand",
        message=f"{city} wait time {high_wait:.1f}min {'exceeds' if triggered else 'within'} {t.wait_time_high}min",
        triggered=triggered,
    ))


def _check_city_surge(city: str, high: pd.DataFrame, t: MonitoringThresholds, r: AlertResult) -> None:
    surge = high["surge_multiplier"].mean()
    triggered = surge > t.surge_high

    r.alerts.append(Alert(
        name=f"city_{city}_surge",
        severity=Severity.HIGH if triggered else Severity.INFO,
        metric="avg_surge",
        observed_value=surge,
        threshold=t.surge_high,
        comparison=f"{city} high demand",
        city=city,
        period="high_demand",
        message=f"{city} surge {surge:.2f}x {'exceeds' if triggered else 'within'} {t.surge_high}x",
        triggered=triggered,
    ))
