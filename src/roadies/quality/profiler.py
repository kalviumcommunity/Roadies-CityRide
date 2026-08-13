"""Dataset profiling for Roadies-CityRide.

Generates structured profiles describing the structure, quality, and
business-oriented summaries of the ride-sharing dataset.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class ColumnProfile:
    """Profiling result for a single column."""

    name: str
    dtype: str
    row_count: int
    non_null_count: int
    null_count: int
    null_pct: float
    unique_count: int
    unique_pct: float
    # Numeric-specific
    min: float | None = None
    max: float | None = None
    mean: float | None = None
    median: float | None = None
    std: float | None = None
    p25: float | None = None
    p75: float | None = None
    p95: float | None = None
    # Categorical-specific
    top_values: dict[str, int] = field(default_factory=dict)
    # Datetime-specific
    min_timestamp: str | None = None
    max_timestamp: str | None = None
    n_distinct_dates: int | None = None
    n_distinct_hours: int | None = None


@dataclass
class DatasetProfile:
    """Structured profiling result for the full dataset."""

    # Dataset-level
    total_rows: int
    total_columns: int
    duplicate_rows: int
    unique_ride_ids: int
    n_cities: int
    n_riders: int
    n_drivers: int
    time_range: str
    total_missing_values: int
    pct_rows_with_missing: float
    # Column profiles
    columns: list[ColumnProfile] = field(default_factory=list)
    # Business summaries
    rides_by_city: dict[str, int] = field(default_factory=dict)
    rides_by_demand_level: dict[str, int] = field(default_factory=dict)
    rides_by_outcome: dict[str, int] = field(default_factory=dict)
    rider_cancellation_rate: float = 0.0
    driver_cancellation_rate: float = 0.0
    acceptance_rate: float = 0.0
    completion_rate: float = 0.0
    surge_stats: dict[str, float] = field(default_factory=dict)
    wait_time_stats: dict[str, float] = field(default_factory=dict)

    def summary(self) -> str:
        """Return a human-readable summary."""
        lines = [
            f"Dataset Profile: {self.total_rows:,} rows x {self.total_columns} columns",
            f"Duplicate rows: {self.duplicate_rows:,}",
            f"Unique ride IDs: {self.unique_ride_ids:,}",
            f"Cities: {self.n_cities} ({', '.join(sorted(self.rides_by_city.keys()))})",
            f"Riders: {self.n_riders:,}",
            f"Drivers: {self.n_drivers:,}",
            f"Time range: {self.time_range}",
            f"Total missing values: {self.total_missing_values:,} ({self.pct_rows_with_missing:.1f}% of rows)",
            "",
            "Rides by city:",
        ]
        for city, count in sorted(self.rides_by_city.items()):
            lines.append(f"  {city}: {count:,}")
        lines.append("")
        lines.append("Rides by demand level:")
        for level, count in sorted(self.rides_by_demand_level.items()):
            lines.append(f"  {level}: {count:,}")
        lines.append("")
        lines.append("Rides by outcome:")
        for outcome, count in sorted(self.rides_by_outcome.items()):
            lines.append(f"  {outcome}: {count:,}")
        lines.append("")
        lines.append(f"Acceptance rate: {self.acceptance_rate:.1%}")
        lines.append(f"Completion rate: {self.completion_rate:.1%}")
        lines.append(f"Rider cancellation rate: {self.rider_cancellation_rate:.1%}")
        lines.append(f"Driver cancellation rate: {self.driver_cancellation_rate:.1%}")
        lines.append("")
        lines.append("Surge multiplier stats:")
        for k, v in self.surge_stats.items():
            lines.append(f"  {k}: {v:.2f}")
        lines.append("")
        lines.append("Wait time stats:")
        for k, v in self.wait_time_stats.items():
            lines.append(f"  {k}: {v:.2f} min")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Column profiling
# ---------------------------------------------------------------------------

def _profile_numeric(series: pd.Series) -> dict:
    """Compute numeric statistics for a series."""
    s = series.dropna()
    if s.empty:
        return {"min": None, "max": None, "mean": None, "median": None,
                "std": None, "p25": None, "p75": None, "p95": None}
    return {
        "min": float(s.min()),
        "max": float(s.max()),
        "mean": float(s.mean()),
        "median": float(s.median()),
        "std": float(s.std()) if len(s) > 1 else 0.0,
        "p25": float(s.quantile(0.25)),
        "p75": float(s.quantile(0.75)),
        "p95": float(s.quantile(0.95)),
    }


def _profile_categorical(series: pd.Series, top_n: int = 5) -> dict[str, int]:
    """Return the top N most frequent values and their counts."""
    return series.value_counts().head(top_n).to_dict()


def _profile_datetime(series: pd.Series) -> dict:
    """Compute datetime statistics."""
    s = pd.to_datetime(series.dropna(), errors="coerce").dropna()
    if s.empty:
        return {"min_timestamp": None, "max_timestamp": None,
                "n_distinct_dates": None, "n_distinct_hours": None}
    return {
        "min_timestamp": str(s.min()),
        "max_timestamp": str(s.max()),
        "n_distinct_dates": int(s.dt.date.nunique()),
        "n_distinct_hours": int(s.dt.hour.nunique()),
    }


def _profile_column(series: pd.Series) -> ColumnProfile:
    """Profile a single column."""
    n = len(series)
    non_null = int(series.notna().sum())
    null_count = n - non_null
    null_pct = (null_count / n * 100) if n > 0 else 0.0
    unique = series.nunique()
    unique_pct = (unique / n * 100) if n > 0 else 0.0

    dtype_str = str(series.dtype)

    numeric_stats = {}
    cat_stats = {}
    dt_stats = {}

    if pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(series):
        numeric_stats = _profile_numeric(series)
    elif pd.api.types.is_datetime64_any_dtype(series):
        dt_stats = _profile_datetime(series)
    elif series.dtype == object or pd.api.types.is_string_dtype(series) or pd.api.types.is_bool_dtype(series):
        # Check if it looks like a boolean column stored as string
        unique_vals = set(series.dropna().unique())
        if unique_vals <= {"true", "false", "True", "False", "0", "1"}:
            cat_stats = _profile_categorical(series)
        else:
            cat_stats = _profile_categorical(series)

    return ColumnProfile(
        name=series.name or "unknown",
        dtype=dtype_str,
        row_count=n,
        non_null_count=non_null,
        null_count=null_count,
        null_pct=round(null_pct, 2),
        unique_count=unique,
        unique_pct=round(unique_pct, 2),
        min=numeric_stats.get("min"),
        max=numeric_stats.get("max"),
        mean=numeric_stats.get("mean"),
        median=numeric_stats.get("median"),
        std=numeric_stats.get("std"),
        p25=numeric_stats.get("p25"),
        p75=numeric_stats.get("p75"),
        p95=numeric_stats.get("p95"),
        top_values=cat_stats,
        min_timestamp=dt_stats.get("min_timestamp"),
        max_timestamp=dt_stats.get("max_timestamp"),
        n_distinct_dates=dt_stats.get("n_distinct_dates"),
        n_distinct_hours=dt_stats.get("n_distinct_hours"),
    )


# ---------------------------------------------------------------------------
# Dataset-level profiling
# ---------------------------------------------------------------------------

def _profile_dataset_level(df: pd.DataFrame) -> dict:
    """Compute dataset-level metrics."""
    total_rows = len(df)
    total_cols = len(df.columns)

    # Duplicates
    duplicate_rows = int(df.duplicated().sum())

    # Ride IDs
    unique_ride_ids = int(df["ride_id"].nunique()) if "ride_id" in df.columns else 0

    # Entities
    n_cities = int(df["city"].nunique()) if "city" in df.columns else 0
    n_riders = int(df["rider_id"].nunique()) if "rider_id" in df.columns else 0
    n_drivers = int(df["driver_id"].nunique()) if "driver_id" in df.columns else 0

    # Time range
    if "request_timestamp" in df.columns:
        ts = pd.to_datetime(df["request_timestamp"], errors="coerce")
        time_range = f"{ts.min()} to {ts.max()}"
    else:
        time_range = "N/A"

    # Missing values
    total_missing = int(df.isnull().sum().sum())
    rows_with_missing = int(df.isnull().any(axis=1).sum())
    pct_rows_with_missing = (rows_with_missing / total_rows * 100) if total_rows > 0 else 0.0

    return {
        "total_rows": total_rows,
        "total_columns": total_cols,
        "duplicate_rows": duplicate_rows,
        "unique_ride_ids": unique_ride_ids,
        "n_cities": n_cities,
        "n_riders": n_riders,
        "n_drivers": n_drivers,
        "time_range": time_range,
        "total_missing_values": total_missing,
        "pct_rows_with_missing": round(pct_rows_with_missing, 2),
    }


# ---------------------------------------------------------------------------
# Business-oriented profiling
# ---------------------------------------------------------------------------

def _profile_business(df: pd.DataFrame) -> dict:
    """Compute business-oriented summaries."""
    total = len(df)
    if total == 0:
        return {}

    # Rides by city
    rides_by_city = df["city"].value_counts().to_dict() if "city" in df.columns else {}

    # Rides by demand level
    rides_by_demand = df["demand_level"].value_counts().to_dict() if "demand_level" in df.columns else {}

    # Rides by outcome
    outcome_counts = {}
    if "accepted" in df.columns:
        outcome_counts["accepted"] = int(df["accepted"].sum())
        outcome_counts["not_accepted"] = int((~df["accepted"]).sum())
    if "completed" in df.columns:
        outcome_counts["completed"] = int(df["completed"].sum())
        outcome_counts["not_completed"] = int((~df["completed"]).sum())
    if "cancelled_by_rider" in df.columns:
        outcome_counts["cancelled_by_rider"] = int(df["cancelled_by_rider"].sum())
    if "cancelled_by_driver" in df.columns:
        outcome_counts["cancelled_by_driver"] = int(df["cancelled_by_driver"].sum())

    # Rates
    acceptance_rate = float(df["accepted"].mean()) if "accepted" in df.columns else 0.0
    completion_rate = float(df["completed"].mean()) if "completed" in df.columns else 0.0
    rider_cancel_rate = float(df["cancelled_by_rider"].mean()) if "cancelled_by_rider" in df.columns else 0.0
    driver_cancel_rate = float(df["cancelled_by_driver"].mean()) if "cancelled_by_driver" in df.columns else 0.0

    # Surge stats
    surge_stats = {}
    if "surge_multiplier" in df.columns:
        s = df["surge_multiplier"].dropna()
        if not s.empty:
            surge_stats = {
                "min": float(s.min()),
                "max": float(s.max()),
                "mean": float(s.mean()),
                "median": float(s.median()),
            }

    # Wait time stats
    wait_stats = {}
    if "wait_time_minutes" in df.columns:
        w = df["wait_time_minutes"].dropna()
        if not w.empty:
            wait_stats = {
                "min": float(w.min()),
                "max": float(w.max()),
                "mean": float(w.mean()),
                "median": float(w.median()),
                "p95": float(w.quantile(0.95)),
            }

    return {
        "rides_by_city": rides_by_city,
        "rides_by_demand_level": rides_by_demand,
        "rides_by_outcome": outcome_counts,
        "rider_cancellation_rate": rider_cancel_rate,
        "driver_cancellation_rate": driver_cancel_rate,
        "acceptance_rate": acceptance_rate,
        "completion_rate": completion_rate,
        "surge_stats": surge_stats,
        "wait_time_stats": wait_stats,
    }


# ---------------------------------------------------------------------------
# Main profiling entry point
# ---------------------------------------------------------------------------

def profile_dataset(df: pd.DataFrame) -> DatasetProfile:
    """Profile a ride-sharing dataset.

    Parameters
    ----------
    df:
        The dataset to profile.

    Returns
    -------
    DatasetProfile
        Structured profiling result with column-level and dataset-level metrics.
    """
    dataset_level = _profile_dataset_level(df)
    column_profiles = [_profile_column(df[col]) for col in df.columns]
    business = _profile_business(df)

    return DatasetProfile(
        total_rows=dataset_level["total_rows"],
        total_columns=dataset_level["total_columns"],
        duplicate_rows=dataset_level["duplicate_rows"],
        unique_ride_ids=dataset_level["unique_ride_ids"],
        n_cities=dataset_level["n_cities"],
        n_riders=dataset_level["n_riders"],
        n_drivers=dataset_level["n_drivers"],
        time_range=dataset_level["time_range"],
        total_missing_values=dataset_level["total_missing_values"],
        pct_rows_with_missing=dataset_level["pct_rows_with_missing"],
        columns=column_profiles,
        rides_by_city=business.get("rides_by_city", {}),
        rides_by_demand_level=business.get("rides_by_demand_level", {}),
        rides_by_outcome=business.get("rides_by_outcome", {}),
        rider_cancellation_rate=business.get("rider_cancellation_rate", 0.0),
        driver_cancellation_rate=business.get("driver_cancellation_rate", 0.0),
        acceptance_rate=business.get("acceptance_rate", 0.0),
        completion_rate=business.get("completion_rate", 0.0),
        surge_stats=business.get("surge_stats", {}),
        wait_time_stats=business.get("wait_time_stats", {}),
    )


def save_profile_report(profile: DatasetProfile, path: str | Path) -> None:
    """Save a human-readable profiling report to a Markdown file.

    Parameters
    ----------
    profile:
        The dataset profile to export.
    path:
        Output file path.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Roadies-CityRide Dataset Profile",
        "",
        "> Auto-generated profiling report. Describes the structure and quality of the ride-sharing dataset.",
        "",
        "## Dataset Overview",
        "",
        f"| Metric | Value |",
        f"|---|---|",
        f"| Total rows | {profile.total_rows:,} |",
        f"| Total columns | {profile.total_columns} |",
        f"| Duplicate rows | {profile.duplicate_rows:,} |",
        f"| Unique ride IDs | {profile.unique_ride_ids:,} |",
        f"| Cities | {profile.n_cities} |",
        f"| Riders | {profile.n_riders:,} |",
        f"| Drivers | {profile.n_drivers:,} |",
        f"| Time range | {profile.time_range} |",
        f"| Total missing values | {profile.total_missing_values:,} |",
        f"| Rows with missing values | {profile.pct_rows_with_missing:.1f}% |",
        "",
        "## Rides by City",
        "",
        "| City | Count |",
        "|---|---|",
    ]
    for city, count in sorted(profile.rides_by_city.items()):
        lines.append(f"| {city} | {count:,} |")

    lines.extend([
        "",
        "## Rides by Demand Level",
        "",
        "| Demand Level | Count |",
        "|---|---|",
    ])
    for level, count in sorted(profile.rides_by_demand_level.items()):
        lines.append(f"| {level} | {count:,} |")

    lines.extend([
        "",
        "## Rides by Outcome",
        "",
        "| Outcome | Count |",
        "|---|---|",
    ])
    for outcome, count in sorted(profile.rides_by_outcome.items()):
        lines.append(f"| {outcome} | {count:,} |")

    lines.extend([
        "",
        "## Key Rates",
        "",
        f"- Acceptance rate: {profile.acceptance_rate:.1%}",
        f"- Completion rate: {profile.completion_rate:.1%}",
        f"- Rider cancellation rate: {profile.rider_cancellation_rate:.1%}",
        f"- Driver cancellation rate: {profile.driver_cancellation_rate:.1%}",
        "",
        "## Surge Pricing",
        "",
    ])
    if profile.surge_stats:
        lines.extend([
            "| Stat | Value |",
            "|---|---|",
            f"| Min | {profile.surge_stats['min']:.2f} |",
            f"| Max | {profile.surge_stats['max']:.2f} |",
            f"| Mean | {profile.surge_stats['mean']:.2f} |",
            f"| Median | {profile.surge_stats['median']:.2f} |",
        ])

    lines.extend([
        "",
        "## Wait Time",
        "",
    ])
    if profile.wait_time_stats:
        lines.extend([
            "| Stat | Value (min) |",
            "|---|---|",
            f"| Min | {profile.wait_time_stats['min']:.2f} |",
            f"| Max | {profile.wait_time_stats['max']:.2f} |",
            f"| Mean | {profile.wait_time_stats['mean']:.2f} |",
            f"| Median | {profile.wait_time_stats['median']:.2f} |",
            f"| P95 | {profile.wait_time_stats['p95']:.2f} |",
        ])

    lines.extend([
        "",
        "## Column Profiles",
        "",
        "| Column | Dtype | Non-Null | Null % | Unique | Unique % |",
        "|---|---|---|---|---|---|",
    ])
    for col in profile.columns:
        lines.append(
            f"| {col.name} | {col.dtype} | {col.non_null_count:,} | "
            f"{col.null_pct:.1f}% | {col.unique_count:,} | {col.unique_pct:.1f}% |"
        )

    # Numeric detail
    numeric_cols = [c for c in profile.columns if c.min is not None]
    if numeric_cols:
        lines.extend([
            "",
            "## Numeric Column Statistics",
            "",
            "| Column | Min | Max | Mean | Median | Std | P25 | P75 | P95 |",
            "|---|---|---|---|---|---|---|---|---|",
        ])
        for col in numeric_cols:
            lines.append(
                f"| {col.name} | {col.min:.2f} | {col.max:.2f} | {col.mean:.2f} | "
                f"{col.median:.2f} | {col.std:.2f} | {col.p25:.2f} | {col.p75:.2f} | {col.p95:.2f} |"
            )

    # Categorical detail
    cat_cols = [c for c in profile.columns if c.top_values and c.min is None]
    if cat_cols:
        lines.extend([
            "",
            "## Categorical Column Top Values",
            "",
        ])
        for col in cat_cols:
            lines.append(f"### {col.name}")
            lines.append("")
            lines.append("| Value | Count |")
            lines.append("|---|---|")
            for val, count in col.top_values.items():
                lines.append(f"| {val} | {count:,} |")
            lines.append("")

    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
