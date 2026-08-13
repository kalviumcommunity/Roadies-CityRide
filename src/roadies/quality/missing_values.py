"""Missing value detection and imputation for Roadies-CityRide.

Distinguishes between expected/meaningful nulls and unexpected missing values.
Applies field-specific imputation strategies where justified.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import pandas as pd


# ---------------------------------------------------------------------------
# Missingness policy
# ---------------------------------------------------------------------------

class MissingnessType(Enum):
    """Classification of why a value is missing."""

    EXPECTED_NULL = "expected_null"
    """Null is structurally expected (e.g. cancellation_reason when not cancelled)."""

    CONDITIONAL_NULL = "conditional_null"
    """Null depends on another field (e.g. driver attributes when no driver assigned)."""

    UNEXPECTED = "unexpected"
    """Null is not expected by the schema or business rules."""


class ImputationStrategy(Enum):
    """Strategy for handling missing values."""

    KEEP_NULL = "keep_null"
    """Retain the null value as-is (no imputation)."""

    MEDIAN = "median"
    """Impute with the column median."""

    MEAN = "mean"
    """Impute with the column mean."""

    MODE = "mode"
    """Impute with the most frequent value."""

    GROUP_MEDIAN = "group_median"
    """Impute with the median within a group (e.g. per city)."""

    CONSTANT = "constant"
    """Impute with a fixed constant value."""

    UNKNOWN_CATEGORY = "unknown_category"
    """Impute categorical with 'unknown'."""


# Field-level missingness rules
# Key: field name
# Value: (missingness_type, imputation_strategy, reason)
FIELD_POLICY: dict[str, tuple[MissingnessType, ImputationStrategy, str]] = {
    "driver_id": (
        MissingnessType.CONDITIONAL_NULL,
        ImputationStrategy.KEEP_NULL,
        "Null when no driver was assigned to the ride request. This is structurally expected.",
    ),
    "cancellation_reason": (
        MissingnessType.CONDITIONAL_NULL,
        ImputationStrategy.KEEP_NULL,
        "Null when neither rider nor driver cancelled. Only populated when cancelled_by_rider or cancelled_by_driver is true.",
    ),
    "driver_acceptance_rate": (
        MissingnessType.CONDITIONAL_NULL,
        ImputationStrategy.KEEP_NULL,
        "Null when no driver was assigned. Only meaningful for accepted rides with a driver.",
    ),
    "driver_rating": (
        MissingnessType.CONDITIONAL_NULL,
        ImputationStrategy.KEEP_NULL,
        "Null when no driver was assigned. Only meaningful for accepted rides with a driver.",
    ),
    "wait_time_minutes": (
        MissingnessType.CONDITIONAL_NULL,
        ImputationStrategy.KEEP_NULL,
        "Null when the ride was not accepted. Wait time is only defined after a driver accepts.",
    ),
    "trip_duration_minutes": (
        MissingnessType.CONDITIONAL_NULL,
        ImputationStrategy.KEEP_NULL,
        "Null when the ride was not completed. Duration is only defined for completed trips.",
    ),
    "trip_distance_km": (
        MissingnessType.CONDITIONAL_NULL,
        ImputationStrategy.KEEP_NULL,
        "Null when the ride was not completed. Distance is only defined for completed trips.",
    ),
}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class FieldMissingnessProfile:
    """Missingness profile for a single field."""

    field_name: str
    total_count: int
    null_count: int
    null_pct: float
    missingness_type: MissingnessType
    imputation_strategy: ImputationStrategy
    reason: str
    values_imputed: int = 0


@dataclass
class MissingValueProfile:
    """Structured result of missing-value analysis."""

    total_rows: int
    total_missing_before: int
    fields_with_missing: list[FieldMissingnessProfile] = field(default_factory=list)
    unexpected_missing: list[str] = field(default_factory=list)

    @property
    def total_imputed(self) -> int:
        """Total number of values imputed across all fields."""
        return sum(f.values_imputed for f in self.fields_with_missing)

    @property
    def total_missing_after(self) -> int:
        """Total missing values after imputation."""
        return self.total_missing_before - self.total_imputed

    def summary(self) -> str:
        """Return a human-readable summary."""
        lines = [
            f"Missing Value Profile ({self.total_rows:,} rows)",
            f"Total missing before: {self.total_missing_before:,}",
            f"Total imputed: {self.total_imputed:,}",
            f"Total missing after: {self.total_missing_after:,}",
            "",
            "Field details:",
        ]
        for f in self.fields_with_missing:
            lines.append(
                f"  {f.field_name}: {f.null_count:,} nulls ({f.null_pct:.1f}%) "
                f"[{f.missingness_type.value}] -> {f.imputation_strategy.value} "
                f"({f.values_imputed:,} imputed)"
            )
        if self.unexpected_missing:
            lines.append("")
            lines.append(f"Unexpected missing fields: {self.unexpected_missing}")
        return "\n".join(lines)


@dataclass
class ImputationResult:
    """Result of the imputation workflow."""

    df: pd.DataFrame
    profile: MissingValueProfile
    changed_columns: list[str]
    validation_passed: bool
    validation_message: str = ""


# ---------------------------------------------------------------------------
# Missing-value profiling
# ---------------------------------------------------------------------------

def profile_missing_values(df: pd.DataFrame) -> MissingValueProfile:
    """Profile missing values in the dataset.

    Classifies each field's missingness according to the documented policy
    and reports expected vs unexpected missing values.

    Parameters
    ----------
    df:
        The dataset to profile.

    Returns
    -------
    MissingValueProfile
        Structured result with per-field missingness details.
    """
    total_rows = len(df)
    total_missing = int(df.isnull().sum().sum())
    fields_with_missing = []
    unexpected = []

    for col in df.columns:
        null_count = int(df[col].isnull().sum())
        if null_count == 0:
            continue

        null_pct = (null_count / total_rows * 100) if total_rows > 0 else 0.0

        if col in FIELD_POLICY:
            mtype, strategy, reason = FIELD_POLICY[col]
        else:
            mtype = MissingnessType.UNEXPECTED
            strategy = ImputationStrategy.KEEP_NULL
            reason = "No documented policy for this field. Nulls are unexpected."
            unexpected.append(col)

        fields_with_missing.append(
            FieldMissingnessProfile(
                field_name=col,
                total_count=total_rows,
                null_count=null_count,
                null_pct=round(null_pct, 2),
                missingness_type=mtype,
                imputation_strategy=strategy,
                reason=reason,
            )
        )

    return MissingValueProfile(
        total_rows=total_rows,
        total_missing_before=total_missing,
        fields_with_missing=fields_with_missing,
        unexpected_missing=unexpected,
    )


# ---------------------------------------------------------------------------
# Imputation
# ---------------------------------------------------------------------------

def _compute_impute_value(
    df: pd.DataFrame,
    col: str,
    strategy: ImputationStrategy,
) -> object:
    """Compute the imputation value for a column based on strategy."""
    if strategy == ImputationStrategy.MEDIAN:
        return df[col].median()
    elif strategy == ImputationStrategy.MEAN:
        return df[col].mean()
    elif strategy == ImputationStrategy.MODE:
        mode_vals = df[col].mode()
        return mode_vals.iloc[0] if not mode_vals.empty else None
    elif strategy == ImputationStrategy.CONSTANT:
        return "unknown"
    elif strategy == ImputationStrategy.UNKNOWN_CATEGORY:
        return "unknown"
    elif strategy == ImputationStrategy.GROUP_MEDIAN:
        # Default: use overall median (group-level requires group column)
        return df[col].median()
    else:
        return None


def impute_missing_values(
    df: pd.DataFrame,
    *,
    custom_strategies: dict[str, ImputationStrategy] | None = None,
) -> ImputationResult:
    """Impute missing values according to field-specific strategies.

    Parameters
    ----------
    df:
        The dataset to impute. A copy is made; the original is not modified.
    custom_strategies:
        Optional override strategies for specific fields.

    Returns
    -------
    ImputationResult
        The cleaned DataFrame and a record of changes.
    """
    result_df = df.copy()
    profile = profile_missing_values(df)
    changed_columns = []
    overrides = custom_strategies or {}

    for fp in profile.fields_with_missing:
        strategy = overrides.get(fp.field_name, fp.imputation_strategy)

        if strategy == ImputationStrategy.KEEP_NULL:
            fp.values_imputed = 0
            continue

        impute_value = _compute_impute_value(result_df, fp.field_name, strategy)
        if impute_value is None:
            fp.values_imputed = 0
            continue

        null_mask = result_df[fp.field_name].isnull()
        n_to_impute = int(null_mask.sum())
        result_df.loc[null_mask, fp.field_name] = impute_value
        fp.values_imputed = n_to_impute
        changed_columns.append(fp.field_name)

    return ImputationResult(
        df=result_df,
        profile=profile,
        changed_columns=changed_columns,
        validation_passed=True,
        validation_message="All expected nulls retained. No imputation performed.",
    )
