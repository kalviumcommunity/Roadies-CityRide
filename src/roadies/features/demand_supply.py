"""Demand and supply feature engineering for Roadies-CityRide.

Creates reusable demand/supply features needed for city-level
operational analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


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
class FeatureEngineeringReport:
    """Report of feature engineering results."""

    features_created: list[str] = field(default_factory=list)
    feature_definitions: list[FeatureDefinition] = field(default_factory=list)
    rows_processed: int = 0

    def summary(self) -> str:
        lines = [
            "Demand/Supply Feature Engineering Report",
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
        name="demand_supply_ratio",
        formula="requested_rides / available_drivers (if available_drivers > 0, else NaN)",
        source_fields=["city_hour_requested_rides", "city_hour_available_drivers"],
        unit="ratio",
        interpretation="Number of requested rides per available driver",
        expected_range="[0, inf)",
    ),
    FeatureDefinition(
        name="supply_pressure",
        formula="available_drivers / requested_rides (if requested_rides > 0, else NaN)",
        source_fields=["city_hour_available_drivers", "city_hour_requested_rides"],
        unit="ratio",
        interpretation="Number of available drivers per requested ride",
        expected_range="[0, inf)",
    ),
    FeatureDefinition(
        name="demand_intensity",
        formula="requested_rides / (requested_rides + available_drivers)",
        source_fields=["city_hour_requested_rides", "city_hour_available_drivers"],
        unit="proportion (0-1)",
        interpretation="Proportion of demand relative to total demand+supply",
        expected_range="[0, 1]",
    ),
    FeatureDefinition(
        name="driver_availability_rate",
        formula="available_drivers / (requested_rides + available_drivers)",
        source_fields=["city_hour_available_drivers", "city_hour_requested_rides"],
        unit="proportion (0-1)",
        interpretation="Proportion of available drivers relative to total",
        expected_range="[0, 1]",
    ),
    FeatureDefinition(
        name="demand_surplus",
        formula="requested_rides - available_drivers",
        source_fields=["city_hour_requested_rides", "city_hour_available_drivers"],
        unit="count",
        interpretation="Excess demand over supply (positive = shortage)",
        expected_range="(-inf, inf)",
    ),
    FeatureDefinition(
        name="surge_pressure",
        formula="(requested_rides - available_drivers) / requested_rides (if > 0, else 0)",
        source_fields=["city_hour_requested_rides", "city_hour_available_drivers"],
        unit="proportion (0-1)",
        interpretation="Normalized demand surplus indicating surge pressure",
        expected_range="[0, 1]",
    ),
]


# ---------------------------------------------------------------------------
# Core feature engineering
# ---------------------------------------------------------------------------

def engineer_demand_supply_features(df: pd.DataFrame) -> tuple[pd.DataFrame, FeatureEngineeringReport]:
    """Create demand and supply features.

    Parameters
    ----------
    df:
        The dataset to enrich. A copy is made; the original is not modified.

    Returns
    -------
    tuple[pd.DataFrame, FeatureEngineeringReport]
        The enriched DataFrame and a report of derived features.
    """
    result = df.copy()
    total = len(result)
    created: list[str] = []

    req = result["city_hour_requested_rides"].astype(float)
    avail = result["city_hour_available_drivers"].astype(float)

    # demand_supply_ratio: requested / available
    result["demand_supply_ratio"] = np.where(avail > 0, req / avail, np.nan)
    created.append("demand_supply_ratio")

    # supply_pressure: available / requested
    result["supply_pressure"] = np.where(req > 0, avail / req, np.nan)
    created.append("supply_pressure")

    # demand_intensity: requested / (requested + available)
    total_demand_supply = req + avail
    result["demand_intensity"] = np.where(
        total_demand_supply > 0, req / total_demand_supply, np.nan
    )
    created.append("demand_intensity")

    # driver_availability_rate: available / (requested + available)
    result["driver_availability_rate"] = np.where(
        total_demand_supply > 0, avail / total_demand_supply, np.nan
    )
    created.append("driver_availability_rate")

    # demand_surplus: requested - available
    result["demand_surplus"] = req - avail
    created.append("demand_surplus")

    # surge_pressure: max(0, surplus / requested)
    result["surge_pressure"] = np.where(
        req > 0, np.maximum(0, (req - avail) / req), np.nan
    )
    created.append("surge_pressure")

    report = FeatureEngineeringReport(
        features_created=created,
        feature_definitions=FEATURE_DEFS,
        rows_processed=total,
    )

    return result, report
