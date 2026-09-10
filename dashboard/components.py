"""Reusable presentation components for the Roadies-CityRide dashboard."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard.theme import (
    BORDER,
    BLUE,
    DANGER,
    MUTED,
    NAVY,
    ORANGE,
    SKY,
    SUCCESS,
    apply_plotly_theme,
)


def render_sidebar_brand() -> None:
    """Render the product identity and pipeline status in the sidebar."""
    st.sidebar.markdown(
        f"""
        <div class="roadies-sidebar-brand">
            <div class="roadies-mark">R</div>
            <div><strong>ROADIES</strong><span>CITYRIDE</span></div>
        </div>
        <div class="roadies-sidebar-kicker">OPERATIONS INTELLIGENCE</div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_status() -> None:
    """Render status indicators backed by the active application state."""
    st.sidebar.markdown(
        """
        <div class="roadies-status-panel">
            <div class="roadies-status-title">SYSTEM STATUS</div>
            <div><span class="roadies-dot roadies-dot-good"></span>DATA PIPELINE <b>CONNECTED</b></div>
            <div><span class="roadies-dot roadies-dot-good"></span>ANALYTICS ENGINE <b>ACTIVE</b></div>
            <div><span class="roadies-dot roadies-dot-good"></span>ANOMALY DETECTION <b>ACTIVE</b></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(eyebrow: str, title: str, description: str) -> None:
    """Render a compact, consistent page header."""
    st.markdown(
        f"""
        <div class="roadies-page-header">
            <div>
                <div class="roadies-eyebrow">{eyebrow}</div>
                <h1>{title}</h1>
                <p>{description}</p>
            </div>
            <div class="roadies-system-pill"><span class="roadies-dot roadies-dot-good"></span>SYSTEM OPERATIONAL</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(eyebrow: str, title: str, description: str = "") -> None:
    """Render a small section heading."""
    detail = f"<p>{description}</p>" if description else ""
    st.markdown(
        f"""
        <div class="roadies-section-header">
            <div class="roadies-eyebrow">{eyebrow}</div>
            <h2>{title}</h2>
            {detail}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_grid(kpis: Iterable, limit: int | None = None) -> None:
    """Render KPI objects using Streamlit metrics in a responsive grid."""
    items = list(kpis)
    if limit:
        items = items[:limit]
    if not items:
        return
    columns = st.columns(min(len(items), 5))
    for index, kpi in enumerate(items):
        with columns[index % len(columns)]:
            st.metric(
                label=kpi.label,
                value=kpi.formatted_value,
                delta=kpi.formatted_comparison or None,
                delta_color="normal" if kpi.higher_is_better else "inverse",
                help=kpi.description,
            )


def render_metric_cards(metrics: list[tuple[str, str, str]]) -> None:
    """Render simple label/value/detail cards."""
    columns = st.columns(min(len(metrics), 4))
    for index, (label, value, detail) in enumerate(metrics):
        with columns[index % len(columns)]:
            st.markdown(
                f"""
                <div class="roadies-stat-card">
                    <div class="roadies-stat-label">{label}</div>
                    <div class="roadies-stat-value">{value}</div>
                    <div class="roadies-stat-detail">{detail}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_chart(fig: go.Figure, height: int | None = None) -> None:
    """Apply the shared chart styling and hide nonessential modebar controls."""
    fig = apply_plotly_theme(fig)
    if height:
        fig.update_layout(height=height)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_status_badge(value: str) -> str:
    """Return an accessible HTML status badge."""
    normalized = str(value).strip().lower()
    label = normalized.upper()
    return f'<span class="roadies-badge roadies-badge-{normalized}">{label}</span>'


def render_styled_table(df: pd.DataFrame, percent_columns: list[str] | None = None) -> None:
    """Render a compact table with friendly numeric formatting."""
    display = df.copy()
    for column in percent_columns or []:
        if column in display:
            display[column] = display[column].map(lambda value: f"{value:.1f}%")
    st.dataframe(display, use_container_width=True, hide_index=True)


def friendly_metric(name: str) -> str:
    """Convert an internal metric name into a user-facing label."""
    labels = {
        "was_accepted": "Acceptance Rate",
        "rider_cancelled": "Rider Cancel Rate",
        "driver_cancelled": "Driver Cancel Rate",
        "wait_time_minutes": "Average Wait Time",
        "surge_multiplier": "Average Surge",
        "demand_supply_ratio": "Demand / Supply Ratio",
        "relative_deviation": "Relative Deviation",
        "risk_score": "Risk Score",
        "anomaly_type": "Anomaly Type",
    }
    return labels.get(name, name.replace("_", " ").title())
