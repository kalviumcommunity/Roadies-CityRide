"""Analysis module for Roadies-CityRide."""

from roadies.analysis.distributions import (
    compute_numerical_stats,
    compute_categorical_stats,
    compare_high_demand,
    compare_cities,
)
from roadies.analysis.relationships import (
    compute_correlations,
    compare_relationships_by_demand,
    compare_relationships_by_city,
)

__all__ = [
    "compute_numerical_stats",
    "compute_categorical_stats",
    "compare_high_demand",
    "compare_cities",
    "compute_correlations",
    "compare_relationships_by_demand",
    "compare_relationships_by_city",
]
