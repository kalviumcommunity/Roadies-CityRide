"""Driver acceptance behaviour feature engineering for Roadies-CityRide.

Creates ride-level features for analysing driver acceptance behaviour
and its relationship with rider experience.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Baseline and thresholds
# ---------------------------------------------------------------------------

ACCEPTANCE_RATE_BASELINE = 0.80  # 80% = expected normal acceptance rate

# Acceptance rate deviation bands
ACCEPTANCE_BANDS: dict[str, tuple[float, float]] = {
    "well_above": (0.10, np.inf),
    "above": (0.05, 0.10),
    "near_baseline": (-0.05, 0.05),
    "below": (-0.10, -0.05),
    "well_below": (-np.inf, -0.10),
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
class AcceptanceFeatureReport:
    """Report of acceptance feature engineering results."""

    features_created: list[str] = field(default_factory=list)
    feature_definitions: list[FeatureDefinition] = field(default_factory=list)
    baseline: float = ACCEPTANCE_RATE_BASELINE
    rows_processed: int = 0

    def summary(self) -> str:
        lines = [
            "Acceptance Feature Engineering Report",
            f"Baseline: {self.baseline}",
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
        name="was_accepted",
        formula="accepted == true",
        source_fields=["accepted"],
        unit="boolean",
        interpretation="Whether this ride was accepted by a driver",
        expected_range="true | false",
    ),
    FeatureDefinition(
        name="was_not_accepted",
        formula="accepted == false",
        source_fields=["accepted"],
        unit="boolean",
        interpretation="Whether this ride was NOT accepted",
        expected_range="true | false",
    ),
    FeatureDefinition(
        name="acceptance_rate_deviation",
        formula="driver_acceptance_rate - 0.80",
        source_fields=["driver_acceptance_rate"],
        unit="proportion (-1 to 1)",
        interpretation="Deviation of assigned driver acceptance rate from baseline",
        expected_range="[-0.80, 0.20]",
    ),
    FeatureDefinition(
        name="acceptance_rate_band",
        formula="categorical band based on deviation from baseline",
        source_fields=["driver_acceptance_rate"],
        unit="category",
        interpretation="Driver acceptance rate relative to baseline",
        expected_range="well_above | above | near_baseline | below | well_below",
    ),
    FeatureDefinition(
        name="has_driver",
        formula="driver_id is not null",
        source_fields=["driver_id"],
        unit="boolean",
        interpretation="Whether a driver was assigned to this ride",
        expected_range="true | false",
    ),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _categorize_acceptance_rate(rate: float) -> str:
    """Assign acceptance rate band based on deviation from baseline."""
    if pd.isna(rate):
        return "unknown"
    deviation = rate - ACCEPTANCE_RATE_BASELINE
    if deviation >= 0.10:
        return "well_above"
    elif deviation >= 0.05:
        return "above"
    elif deviation >= -0.05:
        return "near_baseline"
    elif deviation >= -0.10:
        return "below"
    else:
        return "well_below"


# ---------------------------------------------------------------------------
# Core feature engineering
# ---------------------------------------------------------------------------

def engineer_acceptance_features(df: pd.DataFrame) -> tuple[pd.DataFrame, AcceptanceFeatureReport]:
    """Create driver acceptance behaviour features.

    Parameters
    ----------
    df:
        The dataset to enrich. A copy is made; the original is not modified.

    Returns
    -------
    tuple[pd.DataFrame, AcceptanceFeatureReport]
        The enriched DataFrame and a report of derived features.
    """
    result = df.copy()
    total = len(result)
    created: list[str] = []

    # was_accepted: boolean indicator
    result["was_accepted"] = result["accepted"] == True
    created.append("was_accepted")

    # was_not_accepted: boolean indicator
    result["was_not_accepted"] = result["accepted"] == False
    created.append("was_not_accepted")

    # acceptance_rate_deviation: deviation from baseline
    dar = result["driver_acceptance_rate"]
    result["acceptance_rate_deviation"] = dar - ACCEPTANCE_RATE_BASELINE
    created.append("acceptance_rate_deviation")

    # acceptance_rate_band: categorical band
    result["acceptance_rate_band"] = dar.map(_categorize_acceptance_rate)
    created.append("acceptance_rate_band")

    # has_driver: whether a driver was assigned
    result["has_driver"] = result["driver_id"].notna()
    created.append("has_driver")

    report = AcceptanceFeatureReport(
        features_created=created,
        feature_definitions=FEATURE_DEFS,
        baseline=ACCEPTANCE_RATE_BASELINE,
        rows_processed=total,
    )

    return result, report
