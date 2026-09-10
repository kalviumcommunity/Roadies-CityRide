"""Overview page — Core KPIs and top findings."""

from __future__ import annotations

import streamlit as st

from dashboard.components import (
    render_chart,
    render_kpi_grid,
    render_page_header,
    render_section_header,
    render_styled_table,
)
from dashboard.data_loader import filter_dataframe, load_dashboard_data
from dashboard.filters import render_sidebar_filters
from dashboard.theme import apply_theme
from roadies.analysis.anomaly import classify_risk
from roadies.visualization.kpis import calculate_kpis
from roadies.visualization import plot_city_metric, plot_demand_impact

st.set_page_config(page_title="Overview", page_icon="📊", layout="wide")
apply_theme()

df = load_dashboard_data()

if df.empty:
    st.warning("No data available.")
    st.stop()

filters = render_sidebar_filters(df)
filtered = filter_dataframe(
    df,
    cities=filters["cities"],
    high_demand_only=True if filters["demand_choice"] == "High" else (False if filters["demand_choice"] == "Normal" else None),
    min_surge=filters["surge_range"][0],
    max_surge=filters["surge_range"][1],
)

if filtered.empty:
    st.info("No matching data for selected filters.")
    st.stop()

render_page_header(
    "CITY OPERATIONS",
    "Roadies CityRide",
    "A focused view of rider experience, demand pressure, and operational risk.",
)

# KPI values remain calculated by the shared analytics layer.
kpis = calculate_kpis(filtered)
render_section_header("EXECUTIVE SNAPSHOT", "Core operating signals")
render_kpi_grid(kpis.overall, limit=5)

# High-demand impact
render_section_header("DEMAND PRESSURE", "High-demand impact", "Normal and high-demand outcomes across the active selection.")
if "is_high_demand" in filtered.columns:
    impact_df = filtered.groupby("is_high_demand").agg({
        "was_accepted": "mean",
        "rider_cancelled": "mean",
        "wait_time_minutes": "mean",
        "surge_multiplier": "mean",
    }).reset_index()
    impact_df["demand_period"] = impact_df["is_high_demand"].map({True: "high", False: "normal"})
    impact_df.columns = ["is_high_demand", "acceptance_rate", "rider_cancel_rate", "avg_wait_time", "avg_surge", "demand_period"]
    impact_df[["acceptance_rate", "rider_cancel_rate"]] *= 100

    render_chart(plot_demand_impact(impact_df), height=330)

# City comparison
render_section_header("CITY PERFORMANCE", "Markets requiring attention")
city_df = filtered.groupby("city").agg({
    "was_accepted": "mean",
    "rider_cancelled": "mean",
    "wait_time_minutes": "mean",
    "surge_multiplier": "mean",
}).reset_index()
city_df.columns = ["city", "acceptance_rate", "rider_cancel_rate", "avg_wait_time", "avg_surge"]
city_df[["acceptance_rate", "rider_cancel_rate"]] *= 100

city_display = city_df.copy()
city_display.columns = ["City", "Acceptance", "Rider Cancel", "Avg Wait", "Avg Surge"]
city_display["Acceptance"] = city_display["Acceptance"].map(lambda value: f"{value:.1f}%")
city_display["Rider Cancel"] = city_display["Rider Cancel"].map(lambda value: f"{value:.1f}%")
city_display["Avg Wait"] = city_display["Avg Wait"].map(lambda value: f"{value:.1f} min")
city_display["Avg Surge"] = city_display["Avg Surge"].map(lambda value: f"{value:.2f}x")

left, right = st.columns(2)
with left:
    render_styled_table(city_display)
with right:
    render_chart(plot_city_metric(city_df, "rider_cancel_rate", title="Rider Cancellation by City"), height=330)

