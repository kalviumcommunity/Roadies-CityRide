"""High-demand period classification for Roadies-CityRide.

Classifies ride requests as high-demand based on the 80th percentile
of the demand measure present in the dataset.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HIGH_DEMAND_PERCENTILE = 0.80

DEMAND_MEASURE_COLUMN = "city_hour_requested_rides"


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
class DemandPeriodReport:
    """Report of demand period classification results."""

    features_created: list[str] = field(default_factory=list)
    feature_definitions: list[FeatureDefinition] = field(default_factory=list)
    demand_measure: str = DEMAND_MEASURE_COLUMN
    percentile_threshold: float = HIGH_DEMAND_PERCENTILE
    threshold_value: float = 0.0
    high_demand_count: int = 0
    high_demand_pct: float = 0.0
    rows_processed: int = 0

    def summary(self) -> str:
        lines = [
            "High-Demand Period Classification Report",
            f"Demand measure: {self.demand_measure}",
            f"Percentile threshold: {self.percentile_threshold:.0%}",
            f"Threshold value: {self.threshold_value:.1f}",
            f"Rows processed: {self.rows_processed}",
            f"High-demand rides: {self.high_demand_count} ({self.high_demand_pct:.1f}%)",
        ]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Feature definitions
# ---------------------------------------------------------------------------

FEATURE_DEFS: list[FeatureDefinition] = [
    FeatureDefinition(
        name="demand_percentile",
        formula="percentile rank of city_hour_requested_rides",
        source_fields=["city_hour_requested_rides"],
        unit="proportion (0-1)",
        interpretation="Percentile rank of demand measure for this ride's city-hour",
        expected_range="[0, 1]",
    ),
    FeatureDefinition(
        name="is_high_demand",
        formula="demand_percentile >= 0.80",
        source_fields=["city_hour_requested_rides"],
        unit="boolean",
        interpretation="Whether this ride is in a high-demand period (at or above 80th percentile)",
        expected_range="true | false",
    ),
    FeatureDefinition(
        name="demand_period",
        formula="categorical band based on demand percentile",
        source_fields=["city_hour_requested_rides"],
        unit="category",
        interpretation="Demand period: low (<50th), normal (50th-80th), high (>=80th)",
        expected_range="low | normal | high",
    ),
]


# ---------------------------------------------------------------------------
# Core classification
# ---------------------------------------------------------------------------

def classify_high_demand(df: pd.DataFrame) -> tuple[pd.DataFrame, DemandPeriodReport]:
    """Classify high-demand periods based on 80th percentile of demand.

    Parameters
    ----------
    df:
        The dataset to classify. A copy is made; the original is not modified.

    Returns
    -------
    tuple[pd.DataFrame, DemandPeriodReport]
        The enriched DataFrame and a report of classification results.
    """
    result = df.copy()
    total = len(result)
    created: list[str] = []

    demand = result[DEMAND_MEASURE_COLUMN]

    # Calculate 80th percentile threshold from the dataset
    threshold = float(demand.quantile(HIGH_DEMAND_PERCENTILE))

    # demand_percentile: percentile rank
    result["demand_percentile"] = demand.rank(pct=True)
    created.append("demand_percentile")

    # is_high_demand: boolean flag
    result["is_high_demand"] = demand >= threshold
    created.append("is_high_demand")

    # demand_period: categorical band
    def _demand_period(pct: float) -> str:
        if pd.isna(pct):
            return "unknown"
        if pct < 0.50:
            return "low"
        elif pct < 0.80:
            return "normal"
        else:
            return "high"

    result["demand_period"] = result["demand_percentile"].map(_demand_period)
    created.append("demand_period")

    # Calculate statistics
    high_count = int(result["is_high_demand"].sum())
    high_pct = (high_count / total * 100) if total > 0 else 0.0

    report = DemandPeriodReport(
        features_created=created,
        feature_definitions=FEATURE_DEFS,
        demand_measure=DEMAND_MEASURE_COLUMN,
        percentile_threshold=HIGH_DEMAND_PERCENTILE,
        threshold_value=threshold,
        high_demand_count=high_count,
        high_demand_pct=round(high_pct, 1),
        rows_processed=total,
    )

    return result, report
