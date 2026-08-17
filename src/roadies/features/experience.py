"""Rider experience feature engineering for Roadies-CityRide.

Creates transparent, rule-based rider-experience features that allow
analysing experience degradation without hiding signals behind arbitrary scores.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

# Wait-time severity bands (minutes)
WAIT_TIME_THRESHOLDS: dict[str, tuple[float, float]] = {
    "low": (0.0, 5.0),
    "moderate": (5.0, 15.0),
    "high": (15.0, 30.0),
    "severe": (30.0, float("inf")),
}

# Surge exposure thresholds (multiplier)
SURGE_EXPOSURE_THRESHOLDS: dict[str, tuple[float, float]] = {
    "none": (1.0, 1.0),
    "low": (1.0, 1.5),
    "moderate": (1.5, 2.5),
    "high": (2.5, float("inf")),
}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class FeatureDefinition:
    """Documentation for a derived feature."""

    name: str
    formula: str
    source_fields: list[str]
    unit: str
    interpretation: str
    expected_range: str


@dataclass
class ExperienceFeatureReport:
    """Report of experience feature engineering results."""

    features_created: list[str] = field(default_factory=list)
    feature_definitions: list[FeatureDefinition] = field(default_factory=list)
    rows_processed: int = 0

    def summary(self) -> str:
        lines = [
            "Experience Feature Engineering Report",
            f"Rows processed: {self.rows_processed}",
            f"Features created: {len(self.features_created)}",
            "",
            "Features:",
        ]
        for fd in self.feature_definitions:
            lines.append(f"  {fd.name}: {fd.interpretation}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Feature definitions
# ---------------------------------------------------------------------------

FEATURE_DEFS: list[FeatureDefinition] = [
    FeatureDefinition(
        name="wait_time_severity",
        formula="categorical band based on wait_time_minutes",
        source_fields=["wait_time_minutes"],
        unit="category",
        interpretation="Wait-time severity: low (<5m), moderate (5-15m), high (15-30m), severe (>30m)",
        expected_range="low | moderate | high | severe | unknown",
    ),
    FeatureDefinition(
        name="ride_completed",
        formula="completed == true",
        source_fields=["completed"],
        unit="boolean",
        interpretation="Whether the ride was successfully completed",
        expected_range="true | false",
    ),
    FeatureDefinition(
        name="ride_not_completed",
        formula="completed == false",
        source_fields=["completed"],
        unit="boolean",
        interpretation="Whether the ride was NOT completed",
        expected_range="true | false",
    ),
    FeatureDefinition(
        name="cancellation_type",
        formula="categorical based on cancelled_by_rider and cancelled_by_driver",
        source_fields=["cancelled_by_rider", "cancelled_by_driver"],
        unit="category",
        interpretation="Type of cancellation: none, rider, driver",
        expected_range="none | rider | driver | unknown",
    ),
    FeatureDefinition(
        name="surge_exposure",
        formula="categorical band based on surge_multiplier",
        source_fields=["surge_multiplier"],
        unit="category",
        interpretation="Surge exposure: none (1.0x), low (1.0-1.5x), moderate (1.5-2.5x), high (>2.5x)",
        expected_range="none | low | moderate | high | unknown",
    ),
    FeatureDefinition(
        name="experience_status",
        formula="rule-based classification combining completion, wait, surge, cancellation",
        source_fields=["completed", "wait_time_minutes", "surge_multiplier",
                       "cancelled_by_rider", "cancelled_by_driver"],
        unit="category",
        interpretation="Transparent experience classification",
        expected_range="completed_good | completed_elevated_wait | completed_high_surge | "
                       "rider_cancelled | driver_cancelled | not_accepted | unknown",
    ),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _wait_time_band(wait: float | None) -> str:
    """Classify wait-time severity."""
    if pd.isna(wait):
        return "unknown"
    if wait < 5.0:
        return "low"
    elif wait < 15.0:
        return "moderate"
    elif wait < 30.0:
        return "high"
    else:
        return "severe"


def _surge_exposure_band(surge: float | None) -> str:
    """Classify surge exposure."""
    if pd.isna(surge):
        return "unknown"
    if surge <= 1.0:
        return "none"
    elif surge <= 1.5:
        return "low"
    elif surge <= 2.5:
        return "moderate"
    else:
        return "high"


def _cancellation_type(row: pd.Series) -> str:
    """Classify cancellation type."""
    if pd.isna(row.get("cancelled_by_rider")) or pd.isna(row.get("cancelled_by_driver")):
        return "unknown"
    if row["cancelled_by_rider"] == True:
        return "rider"
    elif row["cancelled_by_driver"] == True:
        return "driver"
    else:
        return "none"


def _experience_status(row: pd.Series) -> str:
    """Classify overall ride experience status."""
    completed = row.get("completed", False)
    rider_cancel = row.get("cancelled_by_rider", False)
    driver_cancel = row.get("cancelled_by_driver", False)
    accepted = row.get("accepted", False)
    wait = row.get("wait_time_minutes")
    surge = row.get("surge_multiplier")

    if rider_cancel == True:
        return "rider_cancelled"
    if driver_cancel == True:
        return "driver_cancelled"
    if accepted == False:
        return "not_accepted"
    if completed == True:
        # Check wait and surge
        wait_sev = _wait_time_band(wait)
        surge_sev = _surge_exposure_band(surge)
        if wait_sev in ("high", "severe"):
            return "completed_elevated_wait"
        if surge_sev in ("moderate", "high"):
            return "completed_high_surge"
        return "completed_good"
    return "unknown"


# ---------------------------------------------------------------------------
# Core feature engineering
# ---------------------------------------------------------------------------

def engineer_experience_features(df: pd.DataFrame) -> tuple[pd.DataFrame, ExperienceFeatureReport]:
    """Create rider experience features.

    Parameters
    ----------
    df:
        The dataset to enrich. A copy is made; the original is not modified.

    Returns
    -------
    tuple[pd.DataFrame, ExperienceFeatureReport]
        The enriched DataFrame and a report of derived features.
    """
    result = df.copy()
    total = len(result)
    created: list[str] = []

    # wait_time_severity: categorical band
    result["wait_time_severity"] = result["wait_time_minutes"].map(_wait_time_band)
    created.append("wait_time_severity")

    # ride_completed: boolean indicator
    result["ride_completed"] = result["completed"] == True
    created.append("ride_completed")

    # ride_not_completed: boolean indicator
    result["ride_not_completed"] = result["completed"] == False
    created.append("ride_not_completed")

    # cancellation_type: categorical
    result["cancellation_type"] = result.apply(_cancellation_type, axis=1)
    created.append("cancellation_type")

    # surge_exposure: categorical band
    result["surge_exposure"] = result["surge_multiplier"].map(_surge_exposure_band)
    created.append("surge_exposure")

    # experience_status: transparent rule-based classification
    result["experience_status"] = result.apply(_experience_status, axis=1)
    created.append("experience_status")

    report = ExperienceFeatureReport(
        features_created=created,
        feature_definitions=FEATURE_DEFS,
        rows_processed=total,
    )

    return result, report
