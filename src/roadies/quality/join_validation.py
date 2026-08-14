"""Multi-source merging and join validation for Roadies-CityRide.

Provides reusable APIs for combining datasets and validating that joins
preserve data integrity and expected cardinality.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class JoinResult:
    """Result of a merge/join operation with validation."""

    left_rows: int
    right_rows: int
    result_rows: int
    join_type: str
    join_keys: list[str]
    unmatched_left: int
    unmatched_right: int
    duplicate_keys_left: int
    duplicate_keys_right: int
    row_multiplication: bool
    match_pct: float
    unmatched_left_ids: list = field(default_factory=list)
    unmatched_right_ids: list = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            "Join Validation Report",
            f"Join type: {self.join_type}",
            f"Join keys: {', '.join(self.join_keys)}",
            f"Left rows: {self.left_rows}",
            f"Right rows: {self.right_rows}",
            f"Result rows: {self.result_rows}",
            f"Unmatched left: {self.unmatched_left}",
            f"Unmatched right: {self.unmatched_right}",
            f"Duplicate keys (left): {self.duplicate_keys_left}",
            f"Duplicate keys (right): {self.duplicate_keys_right}",
            f"Row multiplication: {self.row_multiplication}",
            f"Match %: {self.match_pct:.1f}%",
        ]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def _count_duplicates(df: pd.DataFrame, keys: list[str]) -> int:
    """Count rows involved in duplicate key combinations."""
    if not keys or not all(k in df.columns for k in keys):
        return 0
    dup_mask = df.duplicated(subset=keys, keep=False)
    return int(dup_mask.sum())


def _unmatched_ids(left: pd.DataFrame, right: pd.DataFrame, keys: list[str],
                   side: str) -> list:
    """Find IDs that don't match in the other dataset."""
    merged = pd.merge(left, right, on=keys, how="inner", indicator=True)
    if side == "left":
        left_only = merged[merged["_merge"] == "left_only"]
        id_col = keys[0]
        return left_only[id_col].tolist()[:10]  # limit for report size
    else:
        right_only = merged[merged["_merge"] == "right_only"]
        id_col = keys[0]
        return right_only[id_col].tolist()[:10]


def _count_unmatched(left: pd.DataFrame, right: pd.DataFrame, keys: list[str],
                     side: str) -> int:
    """Count records that don't match."""
    merged = pd.merge(left, right, on=keys, how="outer", indicator=True)
    return int((merged["_merge"] == f"{side}_only").sum())


# ---------------------------------------------------------------------------
# Core merge + validate
# ---------------------------------------------------------------------------

def merge_and_validate(
    left: pd.DataFrame,
    right: pd.DataFrame,
    on: list[str],
    how: str = "left",
    expected_rows: int | None = None,
    left_id_col: str | None = None,
    right_id_col: str | None = None,
) -> JoinResult:
    """Merge two datasets and validate the join.

    Parameters
    ----------
    left, right:
        DataFrames to merge.
    on:
        Join key column(s).
    how:
        Join type (`left`, `inner`, `outer`).
    expected_rows:
        Expected result row count. If set and result differs, row_multiplication=True.
    left_id_col, right_id_col:
        ID columns for reporting unmatched records.

    Returns
    -------
    JoinResult
        Structured report of the join and validation.
    """
    left_rows = len(left)
    right_rows = len(right)

    dup_left = _count_duplicates(left, on)
    dup_right = _count_duplicates(right, on)

    unmatched_l = _count_unmatched(left, right, on, "left")
    unmatched_r = _count_unmatched(left, right, on, "right")

    left_ids = left[left_id_col].tolist()[:10] if left_id_col and left_id_col in left.columns else []
    right_ids = right[right_id_col].tolist()[:10] if right_id_col and right_id_col in right.columns else []

    merged = pd.merge(left, right, on=on, how=how)
    result_rows = len(merged)

    # Detect row multiplication
    row_mult = False
    if expected_rows is not None:
        row_mult = result_rows > expected_rows
    elif how in ("left", "right"):
        ref_rows = left_rows if how == "left" else right_rows
        row_mult = result_rows > ref_rows

    # Match percentage — based on left rows for left joins
    if how == "left":
        match_pct = ((left_rows - unmatched_l) / left_rows * 100) if left_rows > 0 else 100.0
    elif how == "inner":
        match_pct = (result_rows / max(left_rows, right_rows) * 100) if max(left_rows, right_rows) > 0 else 100.0
    else:
        max_possible = max(left_rows, right_rows)
        matched = max_possible - max(unmatched_l, unmatched_r)
        match_pct = (matched / max_possible * 100) if max_possible > 0 else 100.0

    return JoinResult(
        left_rows=left_rows,
        right_rows=right_rows,
        result_rows=result_rows,
        join_type=how,
        join_keys=on,
        unmatched_left=unmatched_l,
        unmatched_right=unmatched_r,
        duplicate_keys_left=dup_left,
        duplicate_keys_right=dup_right,
        row_multiplication=row_mult,
        match_pct=round(match_pct, 1),
        unmatched_left_ids=left_ids,
        unmatched_right_ids=right_ids,
    )


def merge_datasets(
    left: pd.DataFrame,
    right: pd.DataFrame,
    on: list[str],
    how: str = "left",
) -> pd.DataFrame:
    """Simple merge without validation (returns merged DataFrame)."""
    return pd.merge(left, right, on=on, how=how)


def validate_join(
    left: pd.DataFrame,
    right: pd.DataFrame,
    on: list[str],
    how: str = "left",
    expected_rows: int | None = None,
) -> JoinResult:
    """Validate a merge without performing it (returns JoinResult only)."""
    return merge_and_validate(left, right, on, how, expected_rows)
