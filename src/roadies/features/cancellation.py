"""Rider cancellation behaviour feature engineering for Roadies-CityRide.

Creates ride-level features for analysing rider cancellation behaviour
and its relationship with rider experience.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Cancellation reason categories
# ---------------------------------------------------------------------------

CANCELLATION_REASON_CATEGORIES: dict[str, str] = {
    "Long wait time": "wait_related",
    "Driver rude": "driver_behaviour",
    "Changed mind": "rider_decision",
    "Vehicle quality": "vehicle_related",
    "Other": "other",
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
class CancellationFeatureReport:
    """Report of cancellation feature engineering results."""

    features_created: list[str] = field(default_factory=list)
    feature_definitions: list[FeatureDefinition] = field(default_factory=list)
    rows_processed: int = 0

    def summary(self) -> str:
        lines = [
            "Cancellation Feature Engineering Report",
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
        name="rider_cancelled",
        formula="cancelled_by_rider == true",
        source_fields=["cancelled_by_rider"],
        unit="boolean",
        interpretation="Whether the rider cancelled this ride",
        expected_range="true | false",
    ),
    FeatureDefinition(
        name="driver_cancelled",
        formula="cancelled_by_driver == true",
        source_fields=["cancelled_by_driver"],
        unit="boolean",
        interpretation="Whether the driver cancelled this ride",
        expected_range="true | false",
    ),
    FeatureDefinition(
        name="any_cancelled",
        formula="cancelled_by_rider == true OR cancelled_by_driver == true",
        source_fields=["cancelled_by_rider", "cancelled_by_driver"],
        unit="boolean",
        interpretation="Whether any party cancelled the ride",
        expected_range="true | false",
    ),
    FeatureDefinition(
        name="has_cancellation_reason",
        formula="cancellation_reason is not null",
        source_fields=["cancellation_reason"],
        unit="boolean",
        interpretation="Whether a cancellation reason is recorded",
        expected_range="true | false",
    ),
    FeatureDefinition(
        name="cancellation_reason_category",
        formula="mapped from cancellation_reason",
        source_fields=["cancellation_reason"],
        unit="category",
        interpretation="Business category of cancellation reason",
        expected_range="wait_related | driver_behaviour | rider_decision | vehicle_related | other | unknown",
    ),
    FeatureDefinition(
        name="cancelled_before_acceptance",
        formula="cancelled_by_rider == true AND accepted == false",
        source_fields=["cancelled_by_rider", "accepted"],
        unit="boolean",
        interpretation="Rider cancelled before driver accepted",
        expected_range="true | false",
    ),
    FeatureDefinition(
        name="cancelled_after_acceptance",
        formula="(cancelled_by_rider == true OR cancelled_by_driver == true) AND accepted == true",
        source_fields=["cancelled_by_rider", "cancelled_by_driver", "accepted"],
        unit="boolean",
        interpretation="Cancellation happened after driver accepted",
        expected_range="true | false",
    ),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _categorize_reason(reason: str | None) -> str:
    """Map cancellation reason to business category."""
    if pd.isna(reason):
        return "unknown"
    return CANCELLATION_REASON_CATEGORIES.get(reason, "other")


# ---------------------------------------------------------------------------
# Core feature engineering
# ---------------------------------------------------------------------------

def engineer_cancellation_features(df: pd.DataFrame) -> tuple[pd.DataFrame, CancellationFeatureReport]:
    """Create rider cancellation behaviour features.

    Parameters
    ----------
    df:
        The dataset to enrich. A copy is made; the original is not modified.

    Returns
    -------
    tuple[pd.DataFrame, CancellationFeatureReport]
        The enriched DataFrame and a report of derived features.
    """
    result = df.copy()
    total = len(result)
    created: list[str] = []

    # rider_cancelled: boolean indicator
    result["rider_cancelled"] = result["cancelled_by_rider"] == True
    created.append("rider_cancelled")

    # driver_cancelled: boolean indicator
    result["driver_cancelled"] = result["cancelled_by_driver"] == True
    created.append("driver_cancelled")

    # any_cancelled: boolean indicator
    result["any_cancelled"] = (result["cancelled_by_rider"] == True) | (result["cancelled_by_driver"] == True)
    created.append("any_cancelled")

    # has_cancellation_reason: boolean indicator
    result["has_cancellation_reason"] = result["cancellation_reason"].notna()
    created.append("has_cancellation_reason")

    # cancellation_reason_category: mapped business category
    result["cancellation_reason_category"] = result["cancellation_reason"].map(_categorize_reason)
    created.append("cancellation_reason_category")

    # cancelled_before_acceptance: rider cancelled before acceptance
    result["cancelled_before_acceptance"] = (result["cancelled_by_rider"] == True) & (result["accepted"] != True)
    created.append("cancelled_before_acceptance")

    # cancelled_after_acceptance: cancellation after acceptance
    cancelled = (result["cancelled_by_rider"] == True) | (result["cancelled_by_driver"] == True)
    result["cancelled_after_acceptance"] = cancelled & (result["accepted"] == True)
    created.append("cancelled_after_acceptance")

    report = CancellationFeatureReport(
        features_created=created,
        feature_definitions=FEATURE_DEFS,
        rows_processed=total,
    )

    return result, report
