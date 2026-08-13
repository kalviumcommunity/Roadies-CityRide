"""Data-type standardisation for Roadies-CityRide.

Enforces the types defined by the data dictionary so downstream workflows
receive predictable data.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


# ---------------------------------------------------------------------------
# Target schema (mirrors docs/data_dictionary.md)
# ---------------------------------------------------------------------------

# Columns that should be boolean
BOOLEAN_COLUMNS: list[str] = [
    "accepted",
    "completed",
    "cancelled_by_rider",
    "cancelled_by_driver",
]

# Columns that should be integer
INTEGER_COLUMNS: list[str] = [
    "city_hour_requested_rides",
    "city_hour_available_drivers",
]

# Columns that should be float (nullable)
FLOAT_COLUMNS: list[str] = [
    "driver_acceptance_rate",
    "driver_rating",
    "surge_multiplier",
    "base_fare",
    "wait_time_minutes",
    "trip_duration_minutes",
    "trip_distance_km",
]

# Columns that should be string
STRING_COLUMNS: list[str] = [
    "ride_id",
    "rider_id",
    "driver_id",
    "city",
    "demand_level",
    "cancellation_reason",
]

# Columns that should be datetime
DATETIME_COLUMNS: list[str] = [
    "request_timestamp",
]

# All columns in the expected schema
ALL_COLUMNS: list[str] = (
    STRING_COLUMNS
    + BOOLEAN_COLUMNS
    + INTEGER_COLUMNS
    + FLOAT_COLUMNS
    + DATETIME_COLUMNS
)


# ---------------------------------------------------------------------------
# Conversion result
# ---------------------------------------------------------------------------

@dataclass
class ColumnConversion:
    """Result of converting a single column."""

    column: str
    source_dtype: str
    target_dtype: str
    values_converted: int = 0
    conversion_failures: int = 0
    failure_values: list[str] = field(default_factory=list)


@dataclass
class StandardizationResult:
    """Structured result of the standardisation workflow."""

    df: pd.DataFrame
    conversions: list[ColumnConversion] = field(default_factory=list)
    columns_unchanged: list[str] = field(default_factory=list)
    unexpected_columns: list[str] = field(default_factory=list)

    @property
    def total_converted(self) -> int:
        return sum(c.values_converted for c in self.conversions)

    @property
    def total_failures(self) -> int:
        return sum(c.conversion_failures for c in self.conversions)

    def summary(self) -> str:
        lines = [
            f"Standardization result: {self.total_converted} values converted, "
            f"{self.total_failures} failures",
            "",
            "Conversions:",
        ]
        for c in self.conversions:
            status = "OK" if c.conversion_failures == 0 else f"FAIL({c.conversion_failures})"
            lines.append(
                f"  {c.column}: {c.source_dtype} -> {c.target_dtype} "
                f"({c.values_converted} converted) [{status}]"
            )
        if self.columns_unchanged:
            lines.append("")
            lines.append(f"Unchanged: {', '.join(self.columns_unchanged)}")
        if self.unexpected_columns:
            lines.append("")
            lines.append(f"Unexpected columns: {', '.join(self.unexpected_columns)}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Conversion helpers
# ---------------------------------------------------------------------------

def _to_boolean(series: pd.Series, col: str) -> ColumnConversion:
    """Convert a column to boolean, handling strings and numerics."""
    source_dtype = str(series.dtype)
    original = series.copy()

    # Map common representations to bool
    bool_map = {
        "true": True, "false": False,
        "True": True, "False": False,
        "1": True, "0": False,
        "yes": True, "no": False,
    }

    failures = 0
    failure_vals: list[str] = []
    converted = 0

    if series.dtype == bool or series.dtype.name == "bool":
        return ColumnConversion(col, source_dtype, "bool")

    # Try direct conversion first
    try:
        result = series.map(lambda x: bool(x) if pd.notna(x) else None)
        # Count how many changed
        non_null = series.dropna()
        converted = int((non_null.map(lambda x: bool(x)) != original.dropna()).sum())
        return ColumnConversion(
            col, source_dtype, "bool",
            values_converted=converted,
        )
    except (ValueError, TypeError):
        pass

    # Try string mapping
    result = series.copy()
    for idx, val in series.items():
        if pd.isna(val):
            continue
        str_val = str(val).strip()
        if str_val in bool_map:
            result[idx] = bool_map[str_val]
            converted += 1
        else:
            failures += 1
            failure_vals.append(str_val)

    try:
        result = result.astype("boolean")
    except (ValueError, TypeError):
        pass

    return ColumnConversion(
        col, source_dtype, "boolean",
        values_converted=converted,
        conversion_failures=failures,
        failure_values=failure_vals[:10],
    )


def _to_numeric(series: pd.Series, col: str, nullable: bool = False) -> ColumnConversion:
    """Convert a column to numeric (int or float)."""
    source_dtype = str(series.dtype)
    non_null_count = int(series.notna().sum())

    if pd.api.types.is_numeric_dtype(series):
        # Already numeric — check if int conversion needed
        if col in INTEGER_COLUMNS:
            try:
                result = series.copy()
                mask = series.notna()
                result[mask] = series[mask].astype(int)
                return ColumnConversion(col, source_dtype, "int64")
            except (ValueError, TypeError):
                pass
        return ColumnConversion(col, source_dtype, source_dtype)

    # Convert from string/object
    failures = 0
    failure_vals: list[str] = []

    try:
        numeric = pd.to_numeric(series, errors="coerce")
        n_converted = int(series.notna().sum() - numeric.isnull().sum())
        failures = int(n_converted - non_null_count + numeric.notna().sum())
        # Recount properly
        n_original_non_null = int(series.notna().sum())
        n_coerced_non_null = int(numeric.notna().sum())
        n_converted = n_coerced_non_null
        n_failures = n_original_non_null - n_coerced_non_null

        if n_failures > 0:
            mask = series.notna() & numeric.isnull()
            failure_vals = [str(v) for v in series[mask].head(10)]

        if col in INTEGER_COLUMNS:
            try:
                int_mask = numeric.notna()
                numeric[int_mask] = numeric[int_mask].astype(int)
            except (ValueError, TypeError):
                pass

        return ColumnConversion(
            col, source_dtype, str(numeric.dtype),
            values_converted=n_converted,
            conversion_failures=n_failures,
            failure_values=failure_vals,
        )
    except Exception:
        return ColumnConversion(col, source_dtype, source_dtype, conversion_failures=1)


def _to_datetime(series: pd.Series, col: str) -> ColumnConversion:
    """Convert a column to datetime."""
    source_dtype = str(series.dtype)

    if pd.api.types.is_datetime64_any_dtype(series):
        return ColumnConversion(col, source_dtype, "datetime64[ns]")

    try:
        result = pd.to_datetime(series, errors="coerce", format="mixed")
        n_original = int(series.notna().sum())
        n_result = int(result.notna().sum())
        n_failures = n_original - n_result
        failure_vals: list[str] = []
        if n_failures > 0:
            mask = series.notna() & result.isnull()
            failure_vals = [str(v) for v in series[mask].head(10)]

        return ColumnConversion(
            col, source_dtype, "datetime64[ns]",
            values_converted=n_result,
            conversion_failures=n_failures,
            failure_values=failure_vals,
        )
    except Exception:
        return ColumnConversion(col, source_dtype, source_dtype, conversion_failures=1)


def _to_string(series: pd.Series, col: str) -> ColumnConversion:
    """Ensure a column is string type."""
    source_dtype = str(series.dtype)

    if series.dtype == object or pd.api.types.is_string_dtype(series):
        return ColumnConversion(col, source_dtype, "object")

    try:
        result = series.astype(str)
        n_converted = int(series.notna().sum())
        return ColumnConversion(col, source_dtype, "object", values_converted=n_converted)
    except Exception:
        return ColumnConversion(col, source_dtype, source_dtype)


# ---------------------------------------------------------------------------
# Main standardisation entry point
# ---------------------------------------------------------------------------

def standardize_dtypes(df: pd.DataFrame) -> StandardizationResult:
    """Standardise column types according to the data dictionary.

    Parameters
    ----------
    df:
        The dataset to standardise. A copy is made; the original is not modified.

    Returns
    -------
    StandardizationResult
        The standardised DataFrame and a record of conversions.
    """
    result_df = df.copy()
    conversions: list[ColumnConversion] = []
    unchanged: list[str] = []
    unexpected = [c for c in df.columns if c not in ALL_COLUMNS]

    # Boolean columns
    for col in BOOLEAN_COLUMNS:
        if col not in result_df.columns:
            continue
        conv = _to_boolean(result_df[col], col)
        if conv.conversion_failures == 0 and conv.values_converted == 0:
            unchanged.append(col)
        else:
            # Apply the conversion - create new Series to avoid StringArray issues
            bool_map = {"true": True, "false": False, "True": True, "False": False,
                        "1": True, "0": False}
            new_vals = []
            for val in result_df[col]:
                if pd.isna(val):
                    new_vals.append(None)
                else:
                    str_val = str(val).strip()
                    new_vals.append(bool_map.get(str_val, val))
            try:
                result_df[col] = pd.array(new_vals, dtype="boolean")
            except (ValueError, TypeError):
                pass
        conversions.append(conv)

    # Integer columns
    for col in INTEGER_COLUMNS:
        if col not in result_df.columns:
            continue
        conv = _to_numeric(result_df[col], col)
        if conv.conversion_failures == 0 and conv.values_converted == 0:
            unchanged.append(col)
        else:
            numeric = pd.to_numeric(result_df[col], errors="coerce")
            mask = numeric.notna()
            new_vals = result_df[col].tolist()
            for i in range(len(new_vals)):
                if mask.iloc[i]:
                    new_vals[i] = int(numeric.iloc[i])
            result_df[col] = new_vals
        conversions.append(conv)

    # Float columns
    for col in FLOAT_COLUMNS:
        if col not in result_df.columns:
            continue
        conv = _to_numeric(result_df[col], col, nullable=True)
        if conv.conversion_failures == 0 and conv.values_converted == 0:
            unchanged.append(col)
        else:
            result_df[col] = pd.to_numeric(result_df[col], errors="coerce")
        conversions.append(conv)

    # Datetime columns
    for col in DATETIME_COLUMNS:
        if col not in result_df.columns:
            continue
        conv = _to_datetime(result_df[col], col)
        if conv.conversion_failures == 0 and conv.values_converted == 0:
            unchanged.append(col)
        else:
            result_df[col] = pd.to_datetime(result_df[col], errors="coerce", format="mixed")
        conversions.append(conv)

    # String columns (last, to avoid earlier conversions reverting)
    for col in STRING_COLUMNS:
        if col not in result_df.columns:
            continue
        conv = _to_string(result_df[col], col)
        if conv.conversion_failures == 0 and conv.values_converted == 0:
            unchanged.append(col)
        conversions.append(conv)

    return StandardizationResult(
        df=result_df,
        conversions=conversions,
        columns_unchanged=unchanged,
        unexpected_columns=unexpected,
    )
