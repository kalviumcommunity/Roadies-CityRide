"""String cleaning and text normalisation for Roadies-CityRide.

Normalises categorical and textual fields to consistent representations
so that grouping, filtering, and validation treat equivalent values identically.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import pandas as pd


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Textual representations that should be treated as null/missing
TEXTUAL_NULLS: frozenset[str] = frozenset({
    "", " ", "NA", "N/A", "null", "None", "none", "NULL", "nan", "NaN", "NAN",
    "-", "--", "n/a", "na",
})

# Columns to clean (string/categorical fields from the data dictionary)
CLEANABLE_COLUMNS: list[str] = [
    "city",
    "demand_level",
    "cancellation_reason",
    "ride_id",
    "rider_id",
    "driver_id",
]

# Canonical representations for categorical fields (lowercase)
CANONICAL_CITY: dict[str, str] = {
    "mumbai": "Mumbai",
    "delhi": "Delhi",
    "bangalore": "Bangalore",
    "hyderabad": "Hyderabad",
    "chennai": "Chennai",
    "pune": "Pune",
}

CANONICAL_DEMAND: dict[str, str] = {
    "low": "low",
    "medium": "medium",
    "high": "high",
    "critical": "critical",
}

CANONICAL_CANCELLATION: dict[str, str] = {
    "long wait time": "Long wait time",
    "driver rude": "Driver rude",
    "changed mind": "Changed mind",
    "vehicle quality": "Vehicle quality",
    "other": "Other",
}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class ColumnCleaningReport:
    """Report for a single column's cleaning."""

    column: str
    values_changed: int
    textual_nulls_converted: int
    original_values: dict[str, int] = field(default_factory=dict)
    cleaned_values: dict[str, int] = field(default_factory=dict)


@dataclass
class StringCleaningReport:
    """Structured result of the string cleaning workflow."""

    total_values_changed: int
    total_textual_nulls: int
    columns_cleaned: list[ColumnCleaningReport] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            "String Cleaning Report",
            f"Total values changed: {self.total_values_changed}",
            f"Textual nulls converted: {self.total_textual_nulls}",
            "",
            "Columns cleaned:",
        ]
        for c in self.columns_cleaned:
            lines.append(
                f"  {c.column}: {c.values_changed} changed, "
                f"{c.textual_nulls_converted} nulls"
            )
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------

def _normalise_whitespace(s: str) -> str:
    """Collapse repeated internal whitespace and strip leading/trailing."""
    return re.sub(r"\s+", " ", s).strip()


def _is_textual_null(s: str) -> bool:
    """Check if a string represents a missing value."""
    return s.strip() in TEXTUAL_NULLS


def _clean_categorical_value(
    val: str,
    canonical_map: dict[str, str] | None = None,
) -> str:
    """Clean a single categorical value."""
    cleaned = _normalise_whitespace(val)
    if canonical_map and cleaned.lower() in canonical_map:
        return canonical_map[cleaned.lower()]
    return cleaned


# ---------------------------------------------------------------------------
# Main cleaning entry point
# ---------------------------------------------------------------------------

def clean_strings(df: pd.DataFrame) -> tuple[pd.DataFrame, StringCleaningReport]:
    """Clean and normalise string/categorical fields.

    Parameters
    ----------
    df:
        The dataset to clean. A copy is made; the original is not modified.

    Returns
    -------
    tuple[pd.DataFrame, StringCleaningReport]
        The cleaned DataFrame and a report of all changes.
    """
    result_df = df.copy()
    total_changed = 0
    total_nulls = 0
    col_reports: list[ColumnCleaningReport] = []

    # Determine which cleanable columns exist
    cols_to_clean = [c for c in CLEANABLE_COLUMNS if c in result_df.columns]

    for col in cols_to_clean:
        series = result_df[col]
        if not pd.api.types.is_string_dtype(series) and series.dtype != object:
            continue

        values_changed = 0
        textual_nulls = 0
        orig_vals: dict[str, int] = {}
        clean_vals: dict[str, int] = {}

        new_values = []
        for val in series:
            if pd.isna(val):
                new_values.append(val)
                continue

            str_val = str(val)

            # Track original
            orig_vals[str_val] = orig_vals.get(str_val, 0) + 1

            # Check for textual nulls
            if _is_textual_null(str_val):
                textual_nulls += 1
                new_values.append(None)
                continue

            # Apply normalisation
            if col == "city":
                cleaned = _clean_categorical_value(str_val, CANONICAL_CITY)
            elif col == "demand_level":
                cleaned = _clean_categorical_value(str_val, CANONICAL_DEMAND)
            elif col == "cancellation_reason":
                cleaned = _clean_categorical_value(str_val, CANONICAL_CANCELLATION)
            else:
                cleaned = _normalise_whitespace(str_val)

            if cleaned != str_val:
                values_changed += 1

            clean_vals[cleaned] = clean_vals.get(cleaned, 0) + 1
            new_values.append(cleaned)

        result_df[col] = new_values
        total_changed += values_changed
        total_nulls += textual_nulls

        col_reports.append(ColumnCleaningReport(
            column=col,
            values_changed=values_changed,
            textual_nulls_converted=textual_nulls,
            original_values=orig_vals,
            cleaned_values=clean_vals,
        ))

    return result_df, StringCleaningReport(
        total_values_changed=total_changed,
        total_textual_nulls=total_nulls,
        columns_cleaned=col_reports,
    )
