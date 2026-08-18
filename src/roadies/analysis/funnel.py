"""Funnel analysis and drop-off detection for Roadies-CityRide.

Provides reusable APIs for analysing the ride lifecycle funnel:
    ride requested → ride accepted → ride completed
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class FunnelStage:
    """A stage in the funnel."""

    name: str
    count: int
    rate: float  # Rate relative to first stage
    drop_off: int  # Absolute drop from previous stage
    drop_off_pct: float  # Percentage drop from previous stage


@dataclass
class FunnelResult:
    """Complete funnel analysis result."""

    total_requested: int
    stages: list[FunnelStage] = field(default_factory=list)
    group: dict[str, str] = field(default_factory=dict)


@dataclass
class DropOffPoint:
    """A specific drop-off point in the funnel."""

    from_stage: str
    to_stage: str
    count_lost: int
    pct_lost: float
    conversion_rate: float


# ---------------------------------------------------------------------------
# Core funnel analysis
# ---------------------------------------------------------------------------

def analyze_funnel(
    df: pd.DataFrame,
    group_by: list[str] | None = None,
) -> list[FunnelResult]:
    """Analyze the ride lifecycle funnel.

    Parameters
    ----------
    df:
        Ride-level dataset.
    group_by:
        Columns to group by (e.g., ['city']).

    Returns
    -------
    list[FunnelResult]
        Funnel results for each group.
    """
    if group_by:
        # Filter to available columns
        group_by = [c for c in group_by if c in df.columns]
        if not group_by:
            return _single_funnel(df)

        results = []
        for _, group_df in df.groupby(group_by):
            group_vals = {c: group_df[c].iloc[0] if len(group_df) > 0 else None for c in group_by}
            funnel = _single_funnel(group_df)
            if funnel:
                funnel[0].group = group_vals
                results.extend(funnel)
        return results
    else:
        return _single_funnel(df)


def _single_funnel(df: pd.DataFrame) -> list[FunnelResult]:
    """Calculate funnel for a single group."""
    if len(df) == 0:
        return []

    total_requested = len(df)

    # Stage counts
    accepted = int(df["was_accepted"].sum()) if "was_accepted" in df.columns else 0
    completed = int(df["ride_completed"].sum()) if "ride_completed" in df.columns else 0
    rider_cancelled = int(df["rider_cancelled"].sum()) if "rider_cancelled" in df.columns else 0
    driver_cancelled = int(df["driver_cancelled"].sum()) if "driver_cancelled" in df.columns else 0

    stages = [
        FunnelStage(
            name="requested",
            count=total_requested,
            rate=1.0,
            drop_off=0,
            drop_off_pct=0.0,
        ),
        FunnelStage(
            name="accepted",
            count=accepted,
            rate=accepted / total_requested if total_requested > 0 else 0,
            drop_off=total_requested - accepted,
            drop_off_pct=(total_requested - accepted) / total_requested if total_requested > 0 else 0,
        ),
        FunnelStage(
            name="completed",
            count=completed,
            rate=completed / total_requested if total_requested > 0 else 0,
            drop_off=accepted - completed,
            drop_off_pct=(accepted - completed) / accepted if accepted > 0 else 0,
        ),
        FunnelStage(
            name="rider_cancelled",
            count=rider_cancelled,
            rate=rider_cancelled / total_requested if total_requested > 0 else 0,
            drop_off=0,  # Side branch, not sequential
            drop_off_pct=0.0,
        ),
        FunnelStage(
            name="driver_cancelled",
            count=driver_cancelled,
            rate=driver_cancelled / total_requested if total_requested > 0 else 0,
            drop_off=0,  # Side branch
            drop_off_pct=0.0,
        ),
    ]

    return [FunnelResult(total_requested=total_requested, stages=stages)]


def get_drop_off_points(result: FunnelResult) -> list[DropOffPoint]:
    """Extract drop-off points from a funnel result.

    Parameters
    ----------
    result:
        Funnel analysis result.

    Returns
    -------
    list[DropOffPoint]
        Drop-off points.
    """
    drop_offs = []
    stages = result.stages

    # Requested → Accepted
    requested = next((s for s in stages if s.name == "requested"), None)
    accepted = next((s for s in stages if s.name == "accepted"), None)
    if requested and accepted and requested.count > 0:
        drop_offs.append(DropOffPoint(
            from_stage="requested",
            to_stage="accepted",
            count_lost=requested.count - accepted.count,
            pct_lost=(requested.count - accepted.count) / requested.count,
            conversion_rate=accepted.count / requested.count,
        ))

    # Accepted → Completed
    completed = next((s for s in stages if s.name == "completed"), None)
    if accepted and completed and accepted.count > 0:
        drop_offs.append(DropOffPoint(
            from_stage="accepted",
            to_stage="completed",
            count_lost=accepted.count - completed.count,
            pct_lost=(accepted.count - completed.count) / accepted.count,
            conversion_rate=completed.count / accepted.count,
        ))

    return drop_offs


# ---------------------------------------------------------------------------
# Comparative analysis
# ---------------------------------------------------------------------------

def compare_funnels(
    df: pd.DataFrame,
    group_by: list[str],
) -> pd.DataFrame:
    """Compare funnel metrics across groups.

    Parameters
    ----------
    df:
        Dataset.
    group_by:
        Columns to group by.

    Returns
    -------
    pd.DataFrame
        Comparison table.
    """
    results = analyze_funnel(df, group_by)
    if not results:
        return pd.DataFrame()

    rows = []
    for result in results:
        row = result.group.copy()
        for stage in result.stages:
            row[f"{stage.name}_count"] = stage.count
            row[f"{stage.name}_rate"] = stage.rate
        # Add drop-off points
        drop_offs = get_drop_off_points(result)
        for do in drop_offs:
            row[f"{do.from_stage}_to_{do.to_stage}_conversion"] = do.conversion_rate
            row[f"{do.from_stage}_to_{do.to_stage}_drop_off_pct"] = do.pct_lost
        rows.append(row)

    return pd.DataFrame(rows)


def compare_high_demand_funnel(df: pd.DataFrame) -> pd.DataFrame:
    """Compare funnel between high-demand and normal-demand periods.

    Parameters
    ----------
    df:
        Dataset with is_high_demand column.

    Returns
    -------
    pd.DataFrame
        Comparison table.
    """
    if "is_high_demand" not in df.columns:
        return pd.DataFrame()

    high = df[df["is_high_demand"] == True]
    normal = df[df["is_high_demand"] == False]

    high_funnel = analyze_funnel(high)
    normal_funnel = analyze_funnel(normal)

    rows = []
    for label, funnel in [("normal", normal_funnel), ("high", high_funnel)]:
        if not funnel:
            continue
        row = {"demand_period": label}
        for stage in funnel[0].stages:
            row[f"{stage.name}_count"] = stage.count
            row[f"{stage.name}_rate"] = stage.rate
        drop_offs = get_drop_off_points(funnel[0])
        for do in drop_offs:
            row[f"{do.from_stage}_to_{do.to_stage}_conversion"] = do.conversion_rate
        rows.append(row)

    # Calculate changes
    if len(rows) == 2:
        change_row = {"demand_period": "change"}
        for key in rows[0]:
            if key == "demand_period":
                continue
            if isinstance(rows[0][key], (int, float)) and rows[0][key] != 0:
                change_row[key] = rows[1][key] - rows[0][key]
            else:
                change_row[key] = 0
        rows.append(change_row)

    return pd.DataFrame(rows)
