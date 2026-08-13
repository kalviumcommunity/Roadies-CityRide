"""Dataset source validation for Roadies-CityRide.

Validates that an ingested ride-sharing dataset is structurally and logically
suitable before it enters the data-quality pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

# ---------------------------------------------------------------------------
# Schema constants (mirrors docs/data_dictionary.md)
# ---------------------------------------------------------------------------

REQUIRED_COLUMNS: list[str] = [
    "ride_id",
    "rider_id",
    "driver_id",
    "request_timestamp",
    "city",
    "accepted",
    "completed",
    "cancelled_by_rider",
    "cancelled_by_driver",
    "cancellation_reason",
    "driver_acceptance_rate",
    "driver_rating",
    "city_hour_requested_rides",
    "city_hour_available_drivers",
    "demand_level",
    "surge_multiplier",
    "base_fare",
    "wait_time_minutes",
    "trip_duration_minutes",
    "trip_distance_km",
]

CITIES: list[str] = ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Pune"]

DEMAND_LEVELS: list[str] = ["low", "medium", "high", "critical"]

CANCELLATION_REASONS: list[str] = [
    "Long wait time",
    "Driver rude",
    "Changed mind",
    "Vehicle quality",
    "Other",
]

NUMERIC_RANGES: dict[str, tuple[float | None, float | None]] = {
    "driver_acceptance_rate": (0.0, 1.0),
    "driver_rating": (1.0, 5.0),
    "city_hour_requested_rides": (1, 500),
    "city_hour_available_drivers": (0, 300),
    "surge_multiplier": (1.0, 5.0),
    "base_fare": (50.0, 500.0),
    "wait_time_minutes": (0.0, 60.0),
    "trip_duration_minutes": (0.0, 120.0),
    "trip_distance_km": (0.0, 50.0),
}

# Fields that are nullable (can be null in valid data)
NULLABLE_FIELDS: set[str] = {
    "driver_id",
    "cancellation_reason",
    "driver_acceptance_rate",
    "driver_rating",
    "wait_time_minutes",
    "trip_duration_minutes",
    "trip_distance_km",
}


# ---------------------------------------------------------------------------
# Validation result
# ---------------------------------------------------------------------------


@dataclass
class CheckResult:
    """Result of a single validation check."""

    name: str
    passed: bool
    message: str = ""
    details: dict = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Structured result of dataset validation."""

    passed: bool
    checks: list[CheckResult] = field(default_factory=list)
    row_count: int = 0

    @property
    def errors(self) -> list[CheckResult]:
        """Return only failed checks."""
        return [c for c in self.checks if not c.passed]

    def summary(self) -> str:
        """Return a human-readable summary."""
        status = "PASSED" if self.passed else "FAILED"
        lines = [f"Validation {status} ({self.row_count} rows, {len(self.checks)} checks)"]
        for check in self.checks:
            marker = "PASS" if check.passed else "FAIL"
            lines.append(f"  [{marker}] {check.name}: {check.message}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Validation checks
# ---------------------------------------------------------------------------


def _check_not_empty(df: pd.DataFrame) -> CheckResult:
    """Check that the dataset is not empty."""
    count = len(df)
    passed = count > 0
    return CheckResult(
        name="dataset_not_empty",
        passed=passed,
        message=f"{count} rows" if passed else "Dataset is empty",
        details={"row_count": count},
    )


def _check_required_columns(df: pd.DataFrame) -> CheckResult:
    """Check that all required columns exist."""
    actual = set(df.columns)
    missing = set(REQUIRED_COLUMNS) - actual
    extra = actual - set(REQUIRED_COLUMNS)
    passed = len(missing) == 0
    return CheckResult(
        name="required_columns",
        passed=passed,
        message="All required columns present"
        if passed
        else f"Missing: {sorted(missing)}",
        details={"missing": sorted(missing), "extra": sorted(extra)},
    )


def _check_ride_ids_unique(df: pd.DataFrame) -> CheckResult:
    """Check that ride_id values are unique."""
    if "ride_id" not in df.columns:
        return CheckResult(name="ride_ids_unique", passed=False, message="ride_id column missing")
    n_unique = df["ride_id"].nunique()
    n_total = len(df)
    passed = n_unique == n_total
    return CheckResult(
        name="ride_ids_unique",
        passed=passed,
        message=f"All {n_total} ride IDs unique"
        if passed
        else f"{n_total - n_unique} duplicate ride IDs",
        details={"unique_count": n_unique, "total_count": n_total},
    )


def _check_required_identifiers_populated(df: pd.DataFrame) -> CheckResult:
    """Check that ride_id and rider_id are not null."""
    required_id_fields = ["ride_id", "rider_id"]
    null_counts = {}
    for col in required_id_fields:
        if col in df.columns:
            null_counts[col] = int(df[col].isnull().sum())
    all_populated = all(v == 0 for v in null_counts.values())
    return CheckResult(
        name="identifiers_populated",
        passed=all_populated,
        message="All identifiers populated"
        if all_populated
        else f"Null identifiers: {null_counts}",
        details=null_counts,
    )


def _check_categorical_values(df: pd.DataFrame) -> list[CheckResult]:
    """Validate categorical fields against documented categories."""
    results = []

    if "city" in df.columns:
        invalid = set(df["city"].dropna().unique()) - set(CITIES)
        results.append(
            CheckResult(
                name="valid_cities",
                passed=len(invalid) == 0,
                message="All cities valid" if len(invalid) == 0 else f"Invalid cities: {invalid}",
                details={"invalid": sorted(invalid)},
            )
        )

    if "demand_level" in df.columns:
        invalid = set(df["demand_level"].dropna().unique()) - set(DEMAND_LEVELS)
        results.append(
            CheckResult(
                name="valid_demand_levels",
                passed=len(invalid) == 0,
                message="All demand levels valid"
                if len(invalid) == 0
                else f"Invalid demand levels: {invalid}",
                details={"invalid": sorted(invalid)},
            )
        )

    if "cancellation_reason" in df.columns:
        reasons = df["cancellation_reason"].dropna().unique()
        invalid = set(reasons) - set(CANCELLATION_REASONS)
        results.append(
            CheckResult(
                name="valid_cancellation_reasons",
                passed=len(invalid) == 0,
                message="All cancellation reasons valid"
                if len(invalid) == 0
                else f"Invalid reasons: {invalid}",
                details={"invalid": sorted(invalid)},
            )
        )

    # Boolean fields
    for col in ["accepted", "completed", "cancelled_by_rider", "cancelled_by_driver"]:
        if col in df.columns:
            unique_vals = set(df[col].dropna().unique())
            # Accept both bool and numeric 0/1
            valid_bool = {True, False, 0, 1}
            invalid = unique_vals - valid_bool
            results.append(
                CheckResult(
                    name=f"valid_{col}",
                    passed=len(invalid) == 0,
                    message=f"All {col} values boolean"
                    if len(invalid) == 0
                    else f"Invalid {col} values: {invalid}",
                    details={"invalid": sorted(str(v) for v in invalid)},
                )
            )

    return results


def _check_numeric_ranges(df: pd.DataFrame) -> list[CheckResult]:
    """Validate numeric fields are within documented ranges."""
    results = []
    for col, (low, high) in NUMERIC_RANGES.items():
        if col not in df.columns:
            continue
        series = df[col].dropna()
        if series.empty:
            results.append(
                CheckResult(
                    name=f"range_{col}",
                    passed=True,
                    message=f"No non-null values to check",
                )
            )
            continue
        out_of_range = series[(series < low) | (series > high)]
        passed = len(out_of_range) == 0
        results.append(
            CheckResult(
                name=f"range_{col}",
                passed=passed,
                message=f"{col} within [{low}, {high}]"
                if passed
                else f"{len(out_of_range)} values out of range [{low}, {high}]",
                details={"out_of_range_count": len(out_of_range)},
            )
        )
    return results


def _check_logical_constraints(df: pd.DataFrame) -> list[CheckResult]:
    """Validate logical consistency between fields."""
    results = []

    # completed implies accepted
    if {"completed", "accepted"}.issubset(df.columns):
        bad = df[df["completed"] & ~df["accepted"]]
        results.append(
            CheckResult(
                name="completed_implies_accepted",
                passed=len(bad) == 0,
                message="completed => accepted"
                if len(bad) == 0
                else f"{len(bad)} rides completed without acceptance",
                details={"violations": len(bad)},
            )
        )

    # cancelled_by_driver implies accepted
    if {"cancelled_by_driver", "accepted"}.issubset(df.columns):
        bad = df[df["cancelled_by_driver"] & ~df["accepted"]]
        results.append(
            CheckResult(
                name="driver_cancel_implies_accepted",
                passed=len(bad) == 0,
                message="driver_cancel => accepted"
                if len(bad) == 0
                else f"{len(bad)} driver cancellations without acceptance",
                details={"violations": len(bad)},
            )
        )

    # cancelled_by_rider implies not completed
    if {"cancelled_by_rider", "completed"}.issubset(df.columns):
        bad = df[df["cancelled_by_rider"] & df["completed"]]
        results.append(
            CheckResult(
                name="rider_cancel_implies_not_completed",
                passed=len(bad) == 0,
                message="rider_cancel => not completed"
                if len(bad) == 0
                else f"{len(bad)} rider cancellations that completed",
                details={"violations": len(bad)},
            )
        )

    # cancellation_reason should be null when not cancelled
    if "cancellation_reason" in df.columns:
        cancelled = set()
        if "cancelled_by_rider" in df.columns:
            cancelled |= set(df[df["cancelled_by_rider"]].index)
        if "cancelled_by_driver" in df.columns:
            cancelled |= set(df[df["cancelled_by_driver"]].index)

        not_cancelled = set(df.index) - cancelled
        has_reason_when_not_cancelled = df.loc[
            df.index.isin(not_cancelled) & df["cancellation_reason"].notna()
        ]
        results.append(
            CheckResult(
                name="reason_null_when_not_cancelled",
                passed=len(has_reason_when_not_cancelled) == 0,
                message="Reason null when not cancelled"
                if len(has_reason_when_not_cancelled) == 0
                else f"{len(has_reason_when_not_cancelled)} rides with reason but not cancelled",
                details={"violations": len(has_reason_when_not_cancelled)},
            )
        )

    # wait_time_minutes should be null when not accepted
    if {"wait_time_minutes", "accepted"}.issubset(df.columns):
        bad = df[~df["accepted"] & df["wait_time_minutes"].notna()]
        results.append(
            CheckResult(
                name="wait_null_when_not_accepted",
                passed=len(bad) == 0,
                message="wait_time null when not accepted"
                if len(bad) == 0
                else f"{len(bad)} rides with wait_time but not accepted",
                details={"violations": len(bad)},
            )
        )

    # trip fields should be null when not completed
    for col in ["trip_duration_minutes", "trip_distance_km"]:
        if col in df.columns and "completed" in df.columns:
            bad = df[~df["completed"] & df[col].notna()]
            results.append(
                CheckResult(
                    name=f"{col}_null_when_not_completed",
                    passed=len(bad) == 0,
                    message=f"{col} null when not completed"
                    if len(bad) == 0
                    else f"{len(bad)} rides with {col} but not completed",
                    details={"violations": len(bad)},
                )
            )

    return results


# ---------------------------------------------------------------------------
# Main validation entry point
# ---------------------------------------------------------------------------


def validate_dataset(df: pd.DataFrame) -> ValidationResult:
    """Validate a ride-sharing dataset against the documented schema.

    Parameters
    ----------
    df:
        The dataset to validate.

    Returns
    -------
    ValidationResult
        Structured result with pass/fail status and per-check details.
    """
    checks: list[CheckResult] = []

    # Basic integrity
    checks.append(_check_not_empty(df))
    if not checks[-1].passed:
        return ValidationResult(passed=False, checks=checks, row_count=0)

    checks.append(_check_required_columns(df))
    if not checks[-1].passed:
        return ValidationResult(
            passed=False, checks=checks, row_count=len(df)
        )

    checks.append(_check_ride_ids_unique(df))
    checks.append(_check_required_identifiers_populated(df))

    # Categorical values
    checks.extend(_check_categorical_values(df))

    # Numeric ranges
    checks.extend(_check_numeric_ranges(df))

    # Logical constraints
    checks.extend(_check_logical_constraints(df))

    passed = all(c.passed for c in checks)
    return ValidationResult(passed=passed, checks=checks, row_count=len(df))
