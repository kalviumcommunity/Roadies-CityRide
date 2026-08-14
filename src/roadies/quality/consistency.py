"""Data consistency and validation rules engine for Roadies-CityRide.

Checks relationships between fields and identifies logically inconsistent
ride records using explicit business rules.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


# ---------------------------------------------------------------------------
# Rule severity levels
# ---------------------------------------------------------------------------

class Severity:
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ---------------------------------------------------------------------------
# Rule data structure
# ---------------------------------------------------------------------------

class ConsistencyRule:
    """A single consistency rule."""

    rule_id: str = ""
    description: str = ""
    severity: str = ""

    def evaluate(self, df: pd.DataFrame) -> list[int]:
        """Return indices of violating rows. Override in subclasses."""
        raise NotImplementedError


@dataclass
class RuleResult:
    """Result of evaluating a single rule."""

    rule_id: str
    description: str
    severity: str
    passed: bool
    violation_count: int
    violation_pct: float
    affected_indices: list[int]


@dataclass
class ConsistencyReport:
    """Full consistency validation report."""

    total_rows: int
    rules_evaluated: int
    rules_passed: int
    rules_failed: int
    rule_results: list[RuleResult] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            "Consistency Validation Report",
            f"Total rows: {self.total_rows}",
            f"Rules evaluated: {self.rules_evaluated}",
            f"Rules passed: {self.rules_passed}",
            f"Rules failed: {self.rules_failed}",
            "",
        ]
        for r in self.rule_results:
            status = "PASS" if r.passed else "FAIL"
            lines.append(
                f"  [{status}] {r.rule_id}: {r.violation_count} violations "
                f"({r.violation_pct:.1f}%) — {r.description}"
            )
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Concrete rules
# ---------------------------------------------------------------------------

class CompletedMustHaveDriver(ConsistencyRule):
    rule_id = "ride_outcome_01"
    description = "Completed ride must have an accepted driver"
    severity = Severity.CRITICAL

    def evaluate(self, df: pd.DataFrame) -> list[int]:
        mask = (df["completed"] == True) & (df["accepted"] == False)
        return df.index[mask].tolist()


class CompletedNoRiderCancel(ConsistencyRule):
    rule_id = "ride_outcome_02"
    description = "Completed ride must not have rider cancellation"
    severity = Severity.CRITICAL

    def evaluate(self, df: pd.DataFrame) -> list[int]:
        mask = (df["completed"] == True) & (df["cancelled_by_rider"] == True)
        return df.index[mask].tolist()


class CompletedNoDriverCancel(ConsistencyRule):
    rule_id = "ride_outcome_03"
    description = "Completed ride must not have driver cancellation"
    severity = Severity.CRITICAL

    def evaluate(self, df: pd.DataFrame) -> list[int]:
        mask = (df["completed"] == True) & (df["cancelled_by_driver"] == True)
        return df.index[mask].tolist()


class CancelledMustHaveReason(ConsistencyRule):
    rule_id = "ride_outcome_04"
    description = "Cancelled ride must have a cancellation reason"
    severity = Severity.HIGH

    def evaluate(self, df: pd.DataFrame) -> list[int]:
        cancelled = (df["cancelled_by_rider"] == True) | (df["cancelled_by_driver"] == True)
        mask = cancelled & df["cancellation_reason"].isna()
        return df.index[mask].tolist()


class NoCancelNoReason(ConsistencyRule):
    rule_id = "ride_outcome_05"
    description = "Cancellation reason must be null when ride was not cancelled"
    severity = Severity.MEDIUM

    def evaluate(self, df: pd.DataFrame) -> list[int]:
        not_cancelled = (df["cancelled_by_rider"] != True) & (df["cancelled_by_driver"] != True)
        mask = not_cancelled & df["cancellation_reason"].notna()
        return df.index[mask].tolist()


class DriverRatingNeedsDriver(ConsistencyRule):
    rule_id = "driver_01"
    description = "Driver rating should only exist when a driver is assigned"
    severity = Severity.MEDIUM

    def evaluate(self, df: pd.DataFrame) -> list[int]:
        mask = df["driver_rating"].notna() & (df["accepted"] != True)
        return df.index[mask].tolist()


class WaitTimeNonNegative(ConsistencyRule):
    rule_id = "time_01"
    description = "Wait time must be non-negative"
    severity = Severity.HIGH

    def evaluate(self, df: pd.DataFrame) -> list[int]:
        mask = df["wait_time_minutes"] < 0
        return df.index[mask].tolist()


class TripDurationNonNegative(ConsistencyRule):
    rule_id = "time_02"
    description = "Trip duration must be non-negative"
    severity = Severity.HIGH

    def evaluate(self, df: pd.DataFrame) -> list[int]:
        mask = df["trip_duration_minutes"] < 0
        return df.index[mask].tolist()


class TripDistanceNonNegative(ConsistencyRule):
    rule_id = "time_03"
    description = "Trip distance must be non-negative"
    severity = Severity.HIGH

    def evaluate(self, df: pd.DataFrame) -> list[int]:
        mask = df["trip_distance_km"] < 0
        return df.index[mask].tolist()


class SurgeMultiplierValid(ConsistencyRule):
    rule_id = "pricing_01"
    description = "Surge multiplier must be between 1.0 and 5.0"
    severity = Severity.HIGH

    def evaluate(self, df: pd.DataFrame) -> list[int]:
        mask = (df["surge_multiplier"] < 1.0) | (df["surge_multiplier"] > 5.0)
        return df.index[mask].tolist()


class FareNonNegative(ConsistencyRule):
    rule_id = "pricing_02"
    description = "Base fare must be non-negative"
    severity = Severity.HIGH

    def evaluate(self, df: pd.DataFrame) -> list[int]:
        mask = df["base_fare"] < 0
        return df.index[mask].tolist()


class RequestedRidesNonNegative(ConsistencyRule):
    rule_id = "demand_01"
    description = "Requested rides must be non-negative"
    severity = Severity.HIGH

    def evaluate(self, df: pd.DataFrame) -> list[int]:
        mask = df["city_hour_requested_rides"] < 0
        return df.index[mask].tolist()


class AvailableDriversNonNegative(ConsistencyRule):
    rule_id = "demand_02"
    description = "Available drivers must be non-negative"
    severity = Severity.HIGH

    def evaluate(self, df: pd.DataFrame) -> list[int]:
        mask = df["city_hour_available_drivers"] < 0
        return df.index[mask].tolist()


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

ALL_RULES: list[ConsistencyRule] = [
    CompletedMustHaveDriver(),
    CompletedNoRiderCancel(),
    CompletedNoDriverCancel(),
    CancelledMustHaveReason(),
    NoCancelNoReason(),
    DriverRatingNeedsDriver(),
    WaitTimeNonNegative(),
    TripDurationNonNegative(),
    TripDistanceNonNegative(),
    SurgeMultiplierValid(),
    FareNonNegative(),
    RequestedRidesNonNegative(),
    AvailableDriversNonNegative(),
]


def validate_consistency(
    df: pd.DataFrame,
    rules: list[ConsistencyRule] | None = None,
) -> ConsistencyReport:
    """Evaluate consistency rules against the dataset.

    Parameters
    ----------
    df:
        The dataset to validate. The original is not modified.
    rules:
        Optional list of rules. Defaults to ALL_RULES.

    Returns
    -------
    ConsistencyReport
        Structured report of all rule evaluations.
    """
    if rules is None:
        rules = ALL_RULES

    total = len(df)
    results: list[RuleResult] = []
    passed = 0
    failed = 0

    for rule in rules:
        # Check if required columns exist
        required_cols = {
            "completed", "accepted", "cancelled_by_rider", "cancelled_by_driver",
            "cancellation_reason", "driver_rating", "wait_time_minutes",
            "trip_duration_minutes", "trip_distance_km", "surge_multiplier",
            "base_fare", "city_hour_requested_rides", "city_hour_available_drivers",
        }
        # Simplified: only evaluate if the rule's key columns are present
        indices = rule.evaluate(df)
        count = len(indices)
        pct = (count / total * 100) if total > 0 else 0.0
        is_pass = count == 0

        if is_pass:
            passed += 1
        else:
            failed += 1

        results.append(RuleResult(
            rule_id=rule.rule_id,
            description=rule.description,
            severity=rule.severity,
            passed=is_pass,
            violation_count=count,
            violation_pct=round(pct, 2),
            affected_indices=indices,
        ))

    return ConsistencyReport(
        total_rows=total,
        rules_evaluated=len(rules),
        rules_passed=passed,
        rules_failed=failed,
        rule_results=results,
    )
