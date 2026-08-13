"""Date and time transformation pipeline for Roadies-CityRide.

Parses request timestamps into consistent datetime representation and
creates time-derived fields needed by downstream analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TIMESTAMP_COLUMN = "request_timestamp"
TIMEZONE = "UTC"


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class DatetimeTransformReport:
    """Structured report of datetime transformations."""

    total_rows: int
    valid_timestamps: int
    invalid_timestamps: int
    missing_timestamps: int
    derived_columns_created: list[str] = field(default_factory=list)
    timezone: str = TIMEZONE

    def summary(self) -> str:
        lines = [
            "Datetime Transform Report",
            f"Total rows: {self.total_rows}",
            f"Valid timestamps: {self.valid_timestamps}",
            f"Invalid timestamps: {self.invalid_timestamps}",
            f"Missing timestamps: {self.missing_timestamps}",
            f"Timezone: {self.timezone}",
            f"Derived columns: {', '.join(self.derived_columns_created)}",
        ]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Core transformation
# ---------------------------------------------------------------------------

def transform_datetime(df: pd.DataFrame) -> tuple[pd.DataFrame, DatetimeTransformReport]:
    """Parse timestamps and create time-derived fields.

    Parameters
    ----------
    df:
        The dataset to transform. A copy is made; the original is not modified.

    Returns
    -------
    tuple[pd.DataFrame, DatetimeTransformReport]
        The transformed DataFrame and a report of all transformations.
    """
    result_df = df.copy()

    if TIMESTAMP_COLUMN not in result_df.columns:
        return result_df, DatetimeTransformReport(
            total_rows=len(result_df),
            valid_timestamps=0,
            invalid_timestamps=0,
            missing_timestamps=0,
        )

    raw = result_df[TIMESTAMP_COLUMN]
    total = len(raw)

    # Parse timestamps — coerce invalid to NaT
    parsed = pd.to_datetime(raw, errors="coerce", utc=True)

    # Classify
    missing_mask = raw.isna() | (raw.astype(str).str.strip() == "")
    invalid_mask = parsed.isna() & ~missing_mask
    valid_mask = parsed.notna()

    valid_count = int(valid_mask.sum())
    invalid_count = int(invalid_mask.sum())
    missing_count = int(missing_mask.sum())

    result_df[TIMESTAMP_COLUMN] = parsed

    # Derived columns
    derived: list[str] = []

    def _add(col: str, values: pd.Series) -> None:
        result_df[col] = values
        derived.append(col)

    _add("date", parsed.dt.date.astype("string"))
    _add("year", parsed.dt.year.astype("Int64"))
    _add("month", parsed.dt.month.astype("Int64"))
    _add("week", parsed.dt.isocalendar().week.astype("Int64"))
    _add("day_of_month", parsed.dt.day.astype("Int64"))
    _add("day_of_week", parsed.dt.dayofweek.astype("Int64"))
    _add("day_name", parsed.dt.day_name().astype("string"))
    _add("hour", parsed.dt.hour.astype("Int64"))
    _add("is_weekend", (parsed.dt.dayofweek >= 5).astype("boolean"))

    def _period(h: float | int) -> str:
        if pd.isna(h):
            return "unknown"
        if h < 6:
            return "night"
        if h < 12:
            return "morning"
        if h < 17:
            return "afternoon"
        if h < 21:
            return "evening"
        return "night"

    _add("time_period", parsed.dt.hour.map(_period).astype("string"))

    report = DatetimeTransformReport(
        total_rows=total,
        valid_timestamps=valid_count,
        invalid_timestamps=invalid_count,
        missing_timestamps=missing_count,
        derived_columns_created=derived,
        timezone=TIMEZONE,
    )

    return result_df, report
