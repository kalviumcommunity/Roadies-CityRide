"""Surge pricing feature engineering for Roadies-CityRide.

Creates reusable surge-pricing features for analysing pricing pressure
and its relationship with rider/driver behaviour.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Baseline and thresholds
# ---------------------------------------------------------------------------

SURGE_BASELINE = 1.0  # 1.0x = no surge

# Surge category thresholds (multiplier values)
SURGE_BANDS: dict[str, tuple[float, float]] = {
    "no_surge": (1.0, 1.0),
    "low": (1.0, 1.5),
    "moderate": (1.5, 2.5),
    "high": (2.5, 5.0),
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
class SurgeFeatureReport:
    """Report of surge feature engineering results."""

    features_created: list[str] = field(default_factory=list)
    feature_definitions: list[FeatureDefinition] = field(default_factory=list)
    baseline: float = SURGE_BASELINE
    rows_processed: int = 0

    def summary(self) -> str:
        lines = [
            "Surge Feature Engineering Report",
            f"Baseline: {self.baseline}x",
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
        name="surge_deviation",
        formula="surge_multiplier - 1.0",
        source_fields=["surge_multiplier"],
        unit="multiplier units",
        interpretation="Deviation from no-surge baseline (0 = no surge)",
        expected_range="[0, 4.0]",
    ),
    FeatureDefinition(
        name="surge_intensity",
        formula="(surge_multiplier - 1.0) / 4.0",
        source_fields=["surge_multiplier"],
        unit="proportion (0-1)",
        interpretation="Normalized surge level where 0 = no surge, 1 = max surge (5x)",
        expected_range="[0, 1]",
    ),
    FeatureDefinition(
        name="surge_category",
        formula="categorical band based on surge_multiplier",
        source_fields=["surge_multiplier"],
        unit="category",
        interpretation="Surge band: no_surge, low, moderate, high",
        expected_range="no_surge | low | moderate | high",
    ),
    FeatureDefinition(
        name="has_surge",
        formula="surge_multiplier > 1.0",
        source_fields=["surge_multiplier"],
        unit="boolean",
        interpretation="Whether surge pricing is active",
        expected_range="true | false",
    ),
    FeatureDefinition(
        name="surge_to_demand_ratio",
        formula="surge_multiplier / demand_supply_ratio (if available)",
        source_fields=["surge_multiplier", "demand_supply_ratio"],
        unit="ratio",
        interpretation="Surge relative to demand/supply pressure",
        expected_range="[0, inf)",
    ),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _categorize_surge(multiplier: float) -> str:
    """Assign a surge category based on the multiplier value."""
    if pd.isna(multiplier):
        return "unknown"
    if multiplier <= 1.0:
        return "no_surge"
    elif multiplier <= 1.5:
        return "low"
    elif multiplier <= 2.5:
        return "moderate"
    else:
        return "high"


# ---------------------------------------------------------------------------
# Core feature engineering
# ---------------------------------------------------------------------------

def engineer_surge_features(df: pd.DataFrame) -> tuple[pd.DataFrame, SurgeFeatureReport]:
    """Create surge pricing features.

    Parameters
    ----------
    df:
        The dataset to enrich. A copy is made; the original is not modified.

    Returns
    -------
    tuple[pd.DataFrame, SurgeFeatureReport]
        The enriched DataFrame and a report of derived features.
    """
    result = df.copy()
    total = len(result)
    created: list[str] = []

    surge = result["surge_multiplier"]

    # surge_deviation: multiplier - baseline
    result["surge_deviation"] = surge - SURGE_BASELINE
    created.append("surge_deviation")

    # surge_intensity: normalized (0-1) where 1.0=no surge, 5.0=max
    result["surge_intensity"] = (surge - SURGE_BASELINE) / 4.0
    created.append("surge_intensity")

    # surge_category: categorical band
    result["surge_category"] = surge.map(_categorize_surge)
    created.append("surge_category")

    # has_surge: boolean flag
    result["has_surge"] = surge > SURGE_BASELINE
    created.append("has_surge")

    # surge_to_demand_ratio: surge relative to demand pressure
    if "demand_supply_ratio" in result.columns:
        dsr = result["demand_supply_ratio"]
        result["surge_to_demand_ratio"] = np.where(
            dsr > 0, surge / dsr, np.nan
        )
    else:
        result["surge_to_demand_ratio"] = np.nan
    created.append("surge_to_demand_ratio")

    report = SurgeFeatureReport(
        features_created=created,
        feature_definitions=FEATURE_DEFS,
        baseline=SURGE_BASELINE,
        rows_processed=total,
    )

    return result, report
