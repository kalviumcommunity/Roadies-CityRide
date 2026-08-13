"""Duplicate detection and deduplication for Roadies-CityRide.

Detects exact duplicate rows, duplicate ride IDs, and conflicting records.
Applies deterministic deduplication with full reporting.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class DuplicateReport:
    """Structured result of duplicate detection."""

    total_rows: int
    exact_duplicate_count: int
    exact_duplicate_indices: list[int] = field(default_factory=list)
    duplicate_ride_ids: list[str] = field(default_factory=list)
    duplicate_ride_id_count: int = 0
    conflicting_ids: list[str] = field(default_factory=list)
    conflicting_id_count: int = 0
    rows_removed: int = 0
    final_row_count: int = 0

    def summary(self) -> str:
        lines = [
            f"Duplicate Report ({self.total_rows:,} input rows)",
            f"Exact duplicate rows: {self.exact_duplicate_count:,}",
            f"Duplicate ride IDs: {self.duplicate_ride_id_count:,}",
            f"Conflicting records: {self.conflicting_id_count:,}",
            f"Rows removed: {self.rows_removed:,}",
            f"Final row count: {self.final_row_count:,}",
        ]
        if self.conflicting_ids:
            lines.append(f"Conflicting ride IDs: {self.conflicting_ids[:10]}")
        return "\n".join(lines)


@dataclass
class DeduplicationResult:
    """Result of the deduplication workflow."""

    df: pd.DataFrame
    report: DuplicateReport
    conflicts_df: pd.DataFrame | None = None


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------

def detect_duplicates(df: pd.DataFrame) -> DuplicateReport:
    """Detect exact duplicates, duplicate ride IDs, and conflicting records.

    Parameters
    ----------
    df:
        The dataset to check.

    Returns
    -------
    DuplicateReport
        Structured report of all duplicate types found.
    """
    total_rows = len(df)

    # 1. Exact duplicate rows
    exact_dup_mask = df.duplicated(keep="first")
    exact_dup_count = int(exact_dup_mask.sum())
    exact_dup_indices = df.index[exact_dup_mask].tolist()

    # 2. Duplicate ride IDs
    if "ride_id" not in df.columns:
        return DuplicateReport(
            total_rows=total_rows,
            exact_duplicate_count=exact_dup_count,
            exact_duplicate_indices=exact_dup_indices,
            final_row_count=total_rows - exact_dup_count,
            rows_removed=exact_dup_count,
        )

    ride_id_counts = df["ride_id"].value_counts()
    dup_ids = ride_id_counts[ride_id_counts > 1].index.tolist()
    dup_id_count = len(dup_ids)

    # 3. Conflicting records (same ride_id, different values in other columns)
    conflicting: list[str] = []
    if dup_ids:
        non_key_cols = [c for c in df.columns if c != "ride_id"]
        for rid in dup_ids:
            subset = df[df["ride_id"] == rid]
            # Check if all rows for this ride_id are identical
            if not subset.duplicated(keep="first").any():
                # All rows are different (no exact dup within the group)
                # Check if there are actual value differences
                if len(subset) > 1:
                    first_row = subset.iloc[0]
                    has_diff = False
                    for _, row in subset.iloc[1:].iterrows():
                        if not first_row.equals(row):
                            has_diff = True
                            break
                    if has_diff:
                        conflicting.append(rid)
            else:
                # Has both exact dups AND possibly conflicts
                unique_rows = subset.drop_duplicates()
                if len(unique_rows) > 1:
                    conflicting.append(rid)

    return DuplicateReport(
        total_rows=total_rows,
        exact_duplicate_count=exact_dup_count,
        exact_duplicate_indices=exact_dup_indices,
        duplicate_ride_ids=dup_ids,
        duplicate_ride_id_count=dup_id_count,
        conflicting_ids=conflicting,
        conflicting_id_count=len(conflicting),
    )


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

def deduplicate_dataset(df: pd.DataFrame) -> DeduplicationResult:
    """Remove exact duplicates and repeated identical ride-ID records.

    Conflicting records (same ride_id, different values) are retained
    and reported separately. The first occurrence is kept deterministically.

    Parameters
    ----------
    df:
        The dataset to deduplicate. A copy is made; the original is not modified.

    Returns
    -------
    DeduplicationResult
        The deduplicated DataFrame and a full duplicate report.
    """
    report = detect_duplicates(df)
    result_df = df.copy()

    # Step 1: Remove exact duplicate rows
    if report.exact_duplicate_count > 0:
        result_df = result_df.drop_duplicates(keep="first")

    # Step 2: For duplicate ride IDs that are NOT conflicting,
    # keep only the first occurrence (already done by drop_duplicates for identical rows)
    # For non-conflicting duplicate IDs, drop duplicates on ride_id
    if report.duplicate_ride_id_count > 0 and report.conflicting_id_count == 0:
        result_df = result_df.drop_duplicates(subset=["ride_id"], keep="first")

    # Step 3: For conflicting records, keep first occurrence and report
    if report.conflicting_id_count > 0:
        # Extract conflicting records for inspection
        conflicts_df = df[df["ride_id"].isin(report.conflicting_ids)].copy()
        # Keep first occurrence of each ride_id
        result_df = result_df.drop_duplicates(subset=["ride_id"], keep="first")
    else:
        conflicts_df = None

    final_report = DuplicateReport(
        total_rows=report.total_rows,
        exact_duplicate_count=report.exact_duplicate_count,
        exact_duplicate_indices=report.exact_duplicate_indices,
        duplicate_ride_ids=report.duplicate_ride_ids,
        duplicate_ride_id_count=report.duplicate_ride_id_count,
        conflicting_ids=report.conflicting_ids,
        conflicting_id_count=report.conflicting_id_count,
        rows_removed=report.total_rows - len(result_df),
        final_row_count=len(result_df),
    )

    return DeduplicationResult(
        df=result_df,
        report=final_report,
        conflicts_df=conflicts_df,
    )
