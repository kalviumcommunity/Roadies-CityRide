"""Statistical outlier detection for Roadies-CityRide.

Identifies unusual observations in numerical operational variables
without modifying the original data.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Fields to analyse (from data dictionary)
# ---------------------------------------------------------------------------

NUMERIC_FIELDS: list[str] = [
    "surge_multiplier",
    "wait_time_minutes",
    "base_fare",
    "trip_distance_km",
    "trip_duration_minutes",
    "driver_rating",
    "city_hour_available_drivers",
    "city_hour_requested_rides",
    "driver_acceptance_rate",
]


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class FieldOutlierReport:
    """Report for a single field."""

    column: str
    method: str
    lower_threshold: float | None
    upper_threshold: float | None
    outlier_count: int
    outlier_pct: float
    min_val: float
    max_val: float
    median_val: float
    affected_indices: list[int]


@dataclass
class OutlierDetectionReport:
    """Full outlier detection report."""

    total_rows: int
    fields_analysed: list[FieldOutlierReport] = field(default_factory=list)

    def summary(self) -> str:
        lines = ["Outlier Detection Report", f"Total rows: {self.total_rows}", ""]
        for f in self.fields_analysed:
            lines.append(
                f"{f.column} ({f.method}): {f.outlier_count} outliers "
                f"({f.outlier_pct:.1f}%)"
            )
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Detection methods
# ---------------------------------------------------------------------------

def _detect_iqr(series: pd.Series) -> tuple[float | None, float | None, int, list[int]]:
    """Detect outliers using IQR method."""
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    mask = (series < lower) | (series > upper)
    indices = series.index[mask].tolist()
    return float(lower), float(upper), int(mask.sum()), indices


def _detect_zscore(series: pd.Series, threshold: float = 3.0) -> tuple[float | None, float | None, int, list[int]]:
    """Detect outliers using z-score method."""
    mean = series.mean()
    std = series.std()
    if std == 0 or pd.isna(std):
        return None, None, 0, []
    z = (series - mean).abs() / std
    mask = z > threshold
    # thresholds in original units
    lower = float(mean - threshold * std)
    upper = float(mean + threshold * std)
    indices = series.index[mask].tolist()
    return lower, upper, int(mask.sum()), indices


# ---------------------------------------------------------------------------
# Main detection
# ---------------------------------------------------------------------------

def detect_outliers(df: pd.DataFrame) -> OutlierDetectionReport:
    """Detect outliers in numeric fields.

    Parameters
    ----------
    df:
        The dataset to analyse. The original is not modified.

    Returns
    -------
    OutlierDetectionReport
        Structured report of all detected outliers.
    """
    total = len(df)
    reports: list[FieldOutlierReport] = []

    cols = [c for c in NUMERIC_FIELDS if c in df.columns]

    for col in cols:
        series = df[col]
        if not pd.api.types.is_numeric_dtype(series):
            continue

        clean = series.dropna()
        if len(clean) < 3:
            continue

        # Use IQR for most fields; z-score for fare and distance
        if col in ("base_fare", "trip_distance_km"):
            lower, upper, count, indices = _detect_zscore(clean)
            method = "z-score"
        else:
            lower, upper, count, indices = _detect_iqr(clean)
            method = "IQR"

        pct = (count / total * 100) if total > 0 else 0.0

        reports.append(FieldOutlierReport(
            column=col,
            method=method,
            lower_threshold=lower,
            upper_threshold=upper,
            outlier_count=count,
            outlier_pct=round(pct, 2),
            min_val=float(clean.min()),
            max_val=float(clean.max()),
            median_val=float(clean.median()),
            affected_indices=indices,
        ))

    return OutlierDetectionReport(total_rows=total, fields_analysed=reports)
