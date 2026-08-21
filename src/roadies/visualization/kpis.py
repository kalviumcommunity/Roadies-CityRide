"""KPI cards and summary metrics for Roadies-CityRide.

Provides reusable KPI calculation, comparison, and formatting.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import pandas as pd
import plotly.graph_objects as go


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def fmt_pct(value: float, decimals: int = 1) -> str:
    """Format as percentage: 82.4%"""
    return f"{value:.{decimals}f}%"


def fmt_pp(change: float, decimals: int = 1) -> str:
    """Format as percentage-point change: +6.8 pp"""
    sign = "+" if change >= 0 else ""
    return f"{sign}{change:.{decimals}f} pp"


def fmt_minutes(value: float, decimals: int = 1) -> str:
    """Format as minutes: 11.2 min"""
    return f"{value:.{decimals}f} min"


def fmt_multiplier(value: float, decimals: int = 1) -> str:
    """Format as multiplier: 1.8x"""
    return f"{value:.{decimals}f}x"


def fmt_count(value: int) -> str:
    """Format as count: 12,430 rides"""
    return f"{value:,} rides"


# ---------------------------------------------------------------------------
# KPI data structures
# ---------------------------------------------------------------------------

class Direction(str, Enum):
    IMPROVED = "improved"
    DETERIORATED = "deteriorated"
    NEUTRAL = "neutral"


class KPICategory(str, Enum):
    OPERATIONAL = "operational"
    RIDER_EXPERIENCE = "rider_experience"
    HIGH_DEMAND = "high_demand"


@dataclass
class KPI:
    name: str
    value: float
    unit: str
    category: KPICategory
    higher_is_better: bool
    label: str
    description: str
    formatted_value: str
    baseline: float | None = None
    comparison: float | None = None
    comparison_unit: str | None = None
    direction: Direction = Direction.NEUTRAL
    formatted_comparison: str | None = None


@dataclass
class KPISet:
    overall: list[KPI] = field(default_factory=list)
    high_demand: list[KPI] = field(default_factory=list)
    city: dict[str, list[KPI]] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Core KPI calculation
# ---------------------------------------------------------------------------

def calculate_kpis(df: pd.DataFrame) -> KPISet:
    """Calculate core KPIs from ride data.

    Parameters
    ----------
    df:
        DataFrame with ride-level data and precomputed features.

    Returns
    -------
    KPISet
        Structured KPI results.
    """
    total = len(df)
    normal = df[~df["is_high_demand"]] if "is_high_demand" in df.columns else df
    high = df[df["is_high_demand"]] if "is_high_demand" in df.columns else df

    kpis = KPISet()

    # --- Overall operational KPIs ---
    kpis.overall.append(_make_kpi(
        name="total_rides",
        value=float(total),
        unit="count",
        category=KPICategory.OPERATIONAL,
        higher_is_better=False,
        label="Total Rides",
        description="Total ride requests in the dataset",
        formatted_value=fmt_count(total),
    ))

    # Acceptance rate
    ar = df["was_accepted"].mean() * 100
    kpis.overall.append(_make_kpi(
        name="acceptance_rate",
        value=ar,
        unit="percent",
        category=KPICategory.RIDER_EXPERIENCE,
        higher_is_better=True,
        label="Acceptance Rate",
        description="Percentage of rides accepted by drivers",
        formatted_value=fmt_pct(ar),
    ))

    # Rider cancellation rate
    rc = df["rider_cancelled"].mean() * 100
    kpis.overall.append(_make_kpi(
        name="rider_cancel_rate",
        value=rc,
        unit="percent",
        category=KPICategory.RIDER_EXPERIENCE,
        higher_is_better=False,
        label="Rider Cancel Rate",
        description="Percentage of rides cancelled by riders",
        formatted_value=fmt_pct(rc),
    ))

    # Completion rate
    cr = df["was_completed"].mean() * 100 if "was_completed" in df.columns else 0.0
    kpis.overall.append(_make_kpi(
        name="completion_rate",
        value=cr,
        unit="percent",
        category=KPICategory.OPERATIONAL,
        higher_is_better=True,
        label="Completion Rate",
        description="Percentage of rides completed",
        formatted_value=fmt_pct(cr),
    ))

    # Average wait time
    awt = df["wait_time_minutes"].mean() if "wait_time_minutes" in df.columns else 0.0
    kpis.overall.append(_make_kpi(
        name="avg_wait_time",
        value=awt,
        unit="minutes",
        category=KPICategory.RIDER_EXPERIENCE,
        higher_is_better=False,
        label="Avg Wait Time",
        description="Mean wait time for riders",
        formatted_value=fmt_minutes(awt),
    ))

    # Average surge
    asurge = df["surge_multiplier"].mean() if "surge_multiplier" in df.columns else 1.0
    kpis.overall.append(_make_kpi(
        name="avg_surge",
        value=asurge,
        unit="multiplier",
        category=KPICategory.RIDER_EXPERIENCE,
        higher_is_better=False,
        label="Avg Surge",
        description="Mean surge multiplier",
        formatted_value=fmt_multiplier(asurge),
    ))

    # High-demand share
    if "is_high_demand" in df.columns:
        hd_share = df["is_high_demand"].mean() * 100
        kpis.overall.append(_make_kpi(
            name="high_demand_share",
            value=hd_share,
            unit="percent",
            category=KPICategory.HIGH_DEMAND,
            higher_is_better=False,
            label="High Demand Share",
            description="Percentage of rides during high-demand periods",
            formatted_value=fmt_pct(hd_share),
        ))

    # --- High-demand deterioration KPIs ---
    if "is_high_demand" in df.columns and len(high) > 0 and len(normal) > 0:
        kpis.high_demand.extend(_calc_deterioration_kpis(normal, high))

    # --- City-level KPIs ---
    if "city" in df.columns:
        for city_name, city_df in df.groupby("city"):
            kpis.city[city_name] = _calc_city_kpis(city_df, normal, high)

    return kpis


def _make_kpi(**kwargs: object) -> KPI:
    """Construct a KPI with optional defaults."""
    return KPI(**kwargs)  # type: ignore[arg-type]


def _calc_deterioration_kpis(normal: pd.DataFrame, high: pd.DataFrame) -> list[KPI]:
    """Calculate high-demand deterioration KPIs."""
    kpis: list[KPI] = []

    pairs = [
        ("acceptance_rate", "was_accepted", "percent", "Acceptance Deterioration", True),
        ("rider_cancel_rate", "rider_cancelled", "percent", "Rider Cancel Increase", False),
    ]

    if "wait_time_minutes" in normal.columns:
        pairs.append(("avg_wait_time", "wait_time_minutes", "minutes", "Wait Time Increase", False))

    if "surge_multiplier" in normal.columns:
        pairs.append(("avg_surge", "surge_multiplier", "multiplier", "Surge Increase", False))

    for name, col, unit, label, higher_better in pairs:
        normal_val = normal[col].mean() * 100 if unit == "percent" else normal[col].mean()
        high_val = high[col].mean() * 100 if unit == "percent" else high[col].mean()
        change = high_val - normal_val

        if unit == "percent":
            fmt_val = fmt_pct(high_val)
            fmt_comp = fmt_pp(change)
        elif unit == "minutes":
            fmt_val = fmt_minutes(high_val)
            fmt_comp = f"+{change:.1f} min" if change >= 0 else f"{change:.1f} min"
        else:
            fmt_val = fmt_multiplier(high_val)
            fmt_comp = f"+{change:.2f}x" if change >= 0 else f"{change:.2f}x"

        direction = Direction.NEUTRAL
        if abs(change) > 0.01:
            if higher_better:
                direction = Direction.IMPROVED if change > 0 else Direction.DETERIORATED
            else:
                direction = Direction.DETERIORATED if change > 0 else Direction.IMPROVED

        kpis.append(KPI(
            name=name,
            value=high_val,
            unit=unit,
            category=KPICategory.HIGH_DEMAND,
            higher_is_better=higher_better,
            label=label,
            description=f"{label} during high demand",
            formatted_value=fmt_val,
            baseline=normal_val,
            comparison=change,
            comparison_unit="pp" if unit == "percent" else unit,
            direction=direction,
            formatted_comparison=fmt_comp,
        ))

    return kpis


def _calc_city_kpis(
    city_df: pd.DataFrame,
    normal: pd.DataFrame,
    high: pd.DataFrame,
) -> list[KPI]:
    """Calculate city-level KPIs."""
    kpis: list[KPI] = []

    # Core metrics
    ar = city_df["was_accepted"].mean() * 100
    rc = city_df["rider_cancelled"].mean() * 100
    awt = city_df["wait_time_minutes"].mean() if "wait_time_minutes" in city_df.columns else 0.0
    asurge = city_df["surge_multiplier"].mean() if "surge_multiplier" in city_df.columns else 1.0

    # Baselines from overall normal
    normal_ar = normal["was_accepted"].mean() * 100
    normal_rc = normal["rider_cancelled"].mean() * 100
    normal_awt = normal["wait_time_minutes"].mean() if "wait_time_minutes" in normal.columns else 0.0
    normal_asurge = normal["surge_multiplier"].mean() if "surge_multiplier" in normal.columns else 1.0

    metrics = [
        ("acceptance_rate", ar, normal_ar, "percent", "Acceptance Rate", True),
        ("rider_cancel_rate", rc, normal_rc, "percent", "Rider Cancel Rate", False),
        ("avg_wait_time", awt, normal_awt, "minutes", "Avg Wait Time", False),
        ("avg_surge", asurge, normal_asurge, "multiplier", "Avg Surge", False),
    ]

    for name, value, baseline, unit, label, higher_better in metrics:
        change = value - baseline

        if unit == "percent":
            fmt_val = fmt_pct(value)
            fmt_comp = fmt_pp(change)
        elif unit == "minutes":
            fmt_val = fmt_minutes(value)
            fmt_comp = f"+{change:.1f} min" if change >= 0 else f"{change:.1f} min"
        else:
            fmt_val = fmt_multiplier(value)
            fmt_comp = f"+{change:.2f}x" if change >= 0 else f"{change:.2f}x"

        direction = Direction.NEUTRAL
        if abs(change) > 0.01:
            if higher_better:
                direction = Direction.IMPROVED if change > 0 else Direction.DETERIORATED
            else:
                direction = Direction.DETERIORATED if change > 0 else Direction.IMPROVED

        kpis.append(KPI(
            name=name,
            value=value,
            unit=unit,
            category=KPICategory.RIDER_EXPERIENCE,
            higher_is_better=higher_better,
            label=label,
            description=f"{label} for city",
            formatted_value=fmt_val,
            baseline=baseline,
            comparison=change,
            comparison_unit="pp" if unit == "percent" else unit,
            direction=direction,
            formatted_comparison=fmt_comp,
        ))

    return kpis


# ---------------------------------------------------------------------------
# KPI visualisation
# ---------------------------------------------------------------------------

def build_kpi_card_fig(kpi: KPI) -> go.Figure:
    """Build a Plotly Figure representing a single KPI card.

    Parameters
    ----------
    kpi:
        KPI to render.

    Returns
    -------
    go.Figure
        Plotly figure for the KPI card.
    """
    color_map = {
        Direction.IMPROVED: "#2ecc71",
        Direction.DETERIORATED: "#e74c3c",
        Direction.NEUTRAL: "#95a5a6",
    }
    color = color_map[kpi.direction]

    subtitle = ""
    if kpi.formatted_comparison:
        subtitle = f"{kpi.formatted_comparison} vs baseline"

    fig = go.Figure()

    fig.add_annotation(
        text=kpi.formatted_value,
        xref="paper", yref="paper",
        x=0.5, y=0.65,
        showarrow=False,
        font=dict(size=36, color=color),
    )

    fig.add_annotation(
        text=kpi.label,
        xref="paper", yref="paper",
        x=0.5, y=0.35,
        showarrow=False,
        font=dict(size=14, color="#7f8c8d"),
    )

    if subtitle:
        fig.add_annotation(
            text=subtitle,
            xref="paper", yref="paper",
            x=0.5, y=0.15,
            showarrow=False,
            font=dict(size=11, color=color),
        )

    fig.update_layout(
        showlegend=False,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        margin=dict(l=10, r=10, t=10, b=10),
        height=120,
        plot_bgcolor="white",
    )

    return fig


def build_kpi_cards(kpis: list[KPI]) -> list[go.Figure]:
    """Build KPI card figures for a list of KPIs.

    Parameters
    ----------
    kpis:
        List of KPIs.

    Returns
    -------
    list[go.Figure]
        Plotly figures.
    """
    return [build_kpi_card_fig(kpi) for kpi in kpis]
