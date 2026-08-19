"""Root-cause investigation of degraded cities for Roadies-CityRide.

Provides reusable APIs for identifying operational behaviours
associated with rider-experience degradation during high-demand periods.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class DegradedCity:
    """A city identified as degraded during high demand."""

    city: str
    deterioration_score: float
    metrics: dict[str, float] = field(default_factory=dict)


@dataclass
class OperationalLink:
    """A relationship in the operational chain."""

    from_factor: str
    to_factor: str
    correlation: float
    direction: str  # "positive" or "negative"
    strength: str  # "strong", "moderate", "weak"


@dataclass
class CityComparison:
    """Comparison between degraded and stable cities."""

    category: str  # "degraded" or "stable"
    cities: list[str] = field(default_factory=list)
    avg_values: dict[str, float] = field(default_factory=dict)
    deterioration: dict[str, float] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Step 1 — Identify degraded cities
# ---------------------------------------------------------------------------

def identify_degraded_cities(
    df: pd.DataFrame,
    demand_col: str = "is_high_demand",
    city_col: str = "city",
    min_deterioration_threshold: float = 0.15,
) -> list[DegradedCity]:
    """Identify cities with meaningful deterioration during high demand.

    Criteria (must meet at least 3 of 5):
    1. Rider cancellation increase > 15%
    2. Acceptance deterioration > 10%
    3. Completion deterioration > 10%
    4. Wait-time increase > 20%
    5. Surge increase > 25%

    Parameters
    ----------
    df:
        Dataset.
    demand_col:
        High-demand indicator column.
    city_col:
        City column.
    min_deterioration_threshold:
        Minimum deterioration score to flag.

    Returns
    -------
    list[DegradedCity]
        Degraded cities.
    """
    if demand_col not in df.columns or city_col not in df.columns:
        return []

    cities = []
    for city, city_df in df.groupby(city_col):
        high = city_df[city_df[demand_col] == True]
        normal = city_df[city_df[demand_col] == False]

        if len(high) < 10 or len(normal) < 10:
            continue

        # Calculate deterioration
        metrics = {}
        deterioration_flags = 0

        # Rider cancellation
        if "rider_cancelled" in city_df.columns:
            high_cancel = high["rider_cancelled"].mean()
            normal_cancel = normal["rider_cancelled"].mean()
            change = high_cancel - normal_cancel
            metrics["rider_cancel_change"] = float(change)
            if change > 0.05:  # 5 pp increase
                deterioration_flags += 1

        # Acceptance
        if "was_accepted" in city_df.columns:
            high_acc = high["was_accepted"].mean()
            normal_acc = normal["was_accepted"].mean()
            change = normal_acc - high_acc  # Negative means deterioration
            metrics["acceptance_deterioration"] = float(change)
            if change > 0.05:  # 5 pp deterioration
                deterioration_flags += 1

        # Completion
        if "ride_completed" in city_df.columns:
            high_comp = high["ride_completed"].mean()
            normal_comp = normal["ride_completed"].mean()
            change = normal_comp - high_comp
            metrics["completion_deterioration"] = float(change)
            if change > 0.05:
                deterioration_flags += 1

        # Wait time
        if "wait_time_minutes" in city_df.columns:
            high_wait = high["wait_time_minutes"].mean()
            normal_wait = normal["wait_time_minutes"].mean()
            change = (high_wait - normal_wait) / normal_wait if normal_wait > 0 else 0
            metrics["wait_time_increase_pct"] = float(change)
            if change > 0.20:  # 20% increase
                deterioration_flags += 1

        # Surge
        if "surge_multiplier" in city_df.columns:
            high_surge = high["surge_multiplier"].mean()
            normal_surge = normal["surge_multiplier"].mean()
            change = (high_surge - normal_surge) / normal_surge if normal_surge > 0 else 0
            metrics["surge_increase_pct"] = float(change)
            if change > 0.25:  # 25% increase
                deterioration_flags += 1

        # Score: proportion of criteria met
        score = deterioration_flags / 5

        if score >= min_deterioration_threshold:
            cities.append(DegradedCity(
                city=str(city),
                deterioration_score=score,
                metrics=metrics,
            ))

    # Sort by score descending
    cities.sort(key=lambda c: c.deterioration_score, reverse=True)
    return cities


# ---------------------------------------------------------------------------
# Step 2 — Compare degraded vs stable cities
# ---------------------------------------------------------------------------

def compare_degraded_vs_stable(
    df: pd.DataFrame,
    degraded_cities: list[str],
    demand_col: str = "is_high_demand",
    city_col: str = "city",
) -> list[CityComparison]:
    """Compare degraded and stable cities.

    Parameters
    ----------
    df:
        Dataset.
    degraded_cities:
        List of degraded city names.
    demand_col:
        High-demand indicator.
    city_col:
        City column.

    Returns
    -------
    list[CityComparison]
        Comparisons for degraded and stable categories.
    """
    if demand_col not in df.columns or city_col not in df.columns:
        return []

    comparisons = []

    for category, cities in [("degraded", degraded_cities), ("stable", [])]:
        if category == "stable":
            all_cities = df[city_col].unique()
            cities = [c for c in all_cities if c not in degraded_cities]

        # Get high-demand data for these cities
        city_data = df[
            (df[city_col].isin(cities)) & (df[demand_col] == True)
        ]

        if len(city_data) == 0:
            continue

        # Calculate averages
        avg_values = {}
        for col in ["demand_supply_ratio", "was_accepted", "rider_cancelled",
                     "driver_cancelled", "wait_time_minutes", "surge_multiplier",
                     "ride_completed"]:
            if col in city_data.columns:
                avg_values[col] = float(city_data[col].mean())

        # Calculate deterioration (vs normal demand in same cities)
        deterioration = {}
        normal_data = df[
            (df[city_col].isin(cities)) & (df[demand_col] == False)
        ]
        if len(normal_data) > 0:
            for col in ["was_accepted", "rider_cancelled", "wait_time_minutes",
                         "surge_multiplier", "ride_completed"]:
                if col in city_data.columns and col in normal_data.columns:
                    high_val = city_data[col].mean()
                    normal_val = normal_data[col].mean()
                    if col in ["was_accepted", "ride_completed"]:
                        deterioration[col] = float(normal_val - high_val)  # Deterioration
                    elif col in ["rider_cancelled"]:
                        deterioration[col] = float(high_val - normal_val)  # Increase
                    elif col in ["wait_time_minutes", "surge_multiplier"]:
                        deterioration[col] = float(
                            (high_val - normal_val) / normal_val if normal_val > 0 else 0
                        )

        comparisons.append(CityComparison(
            category=category,
            cities=list(cities),
            avg_values=avg_values,
            deterioration=deterioration,
        ))

    return comparisons


# ---------------------------------------------------------------------------
# Step 3 — Trace the operational chain
# ---------------------------------------------------------------------------

def trace_operational_chain(
    df: pd.DataFrame,
    demand_col: str = "is_high_demand",
) -> list[OperationalLink]:
    """Trace relationships in the operational chain.

    Chain:
    demand pressure → supply pressure → acceptance → surge/wait → cancellation

    Parameters
    ----------
    df:
        Dataset.
    demand_col:
        High-demand indicator.

    Returns
    -------
    list[OperationalLink]
        Operational relationships.
    """
    links = []

    # Demand/supply ratio → acceptance
    if "demand_supply_ratio" in df.columns and "was_accepted" in df.columns:
        corr = df["demand_supply_ratio"].corr(df["was_accepted"])
        if not np.isnan(corr):
            links.append(OperationalLink(
                from_factor="demand_supply_ratio",
                to_factor="was_accepted",
                correlation=float(corr),
                direction="negative" if corr < 0 else "positive",
                strength=_correlation_strength(abs(corr)),
            ))

    # Demand/supply ratio → surge
    if "demand_supply_ratio" in df.columns and "surge_multiplier" in df.columns:
        corr = df["demand_supply_ratio"].corr(df["surge_multiplier"])
        if not np.isnan(corr):
            links.append(OperationalLink(
                from_factor="demand_supply_ratio",
                to_factor="surge_multiplier",
                correlation=float(corr),
                direction="positive" if corr > 0 else "negative",
                strength=_correlation_strength(abs(corr)),
            ))

    # Acceptance → wait time
    if "was_accepted" in df.columns and "wait_time_minutes" in df.columns:
        corr = df["was_accepted"].corr(df["wait_time_minutes"])
        if not np.isnan(corr):
            links.append(OperationalLink(
                from_factor="was_accepted",
                to_factor="wait_time_minutes",
                correlation=float(corr),
                direction="negative" if corr < 0 else "positive",
                strength=_correlation_strength(abs(corr)),
            ))

    # Wait time → rider cancellation
    if "wait_time_minutes" in df.columns and "rider_cancelled" in df.columns:
        corr = df["wait_time_minutes"].corr(df["rider_cancelled"])
        if not np.isnan(corr):
            links.append(OperationalLink(
                from_factor="wait_time_minutes",
                to_factor="rider_cancelled",
                correlation=float(corr),
                direction="positive" if corr > 0 else "negative",
                strength=_correlation_strength(abs(corr)),
            ))

    # Surge → rider cancellation
    if "surge_multiplier" in df.columns and "rider_cancelled" in df.columns:
        corr = df["surge_multiplier"].corr(df["rider_cancelled"])
        if not np.isnan(corr):
            links.append(OperationalLink(
                from_factor="surge_multiplier",
                to_factor="rider_cancelled",
                correlation=float(corr),
                direction="positive" if corr > 0 else "negative",
                strength=_correlation_strength(abs(corr)),
            ))

    # Acceptance → completion
    if "was_accepted" in df.columns and "ride_completed" in df.columns:
        corr = df["was_accepted"].corr(df["ride_completed"])
        if not np.isnan(corr):
            links.append(OperationalLink(
                from_factor="was_accepted",
                to_factor="ride_completed",
                correlation=float(corr),
                direction="positive" if corr > 0 else "negative",
                strength=_correlation_strength(abs(corr)),
            ))

    return links


def _correlation_strength(abs_corr: float) -> str:
    """Classify correlation strength."""
    if abs_corr >= 0.5:
        return "strong"
    elif abs_corr >= 0.3:
        return "moderate"
    else:
        return "weak"


# ---------------------------------------------------------------------------
# Step 4 — City-level consistency
# ---------------------------------------------------------------------------

def assess_city_consistency(
    df: pd.DataFrame,
    city_col: str = "city",
    demand_col: str = "is_high_demand",
) -> dict[str, dict[str, float]]:
    """Assess consistency of operational relationships across cities.

    Parameters
    ----------
    df:
        Dataset.
    city_col:
        City column.
    demand_col:
        High-demand indicator.

    Returns
    -------
    dict
        Consistency metrics by city.
    """
    results = {}

    for city, city_df in df.groupby(city_col):
        if "demand_supply_ratio" not in city_df.columns or "rider_cancelled" not in city_df.columns:
            continue

        corr = city_df["demand_supply_ratio"].corr(city_df["rider_cancelled"])
        if not np.isnan(corr):
            if city not in results:
                results[city] = {}
            results[city]["demand_supply_vs_cancel"] = float(corr)

    return results
