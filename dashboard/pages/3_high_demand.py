"""High-Demand Analysis page — Normal vs high-demand impact."""

from __future__ import annotations

import streamlit as st

from dashboard.components import render_chart, render_kpi_grid, render_page_header, render_section_header
from dashboard.data_loader import filter_dataframe, load_dashboard_data
from dashboard.filters import render_sidebar_filters
from dashboard.theme import apply_theme
from roadies.visualization import plot_city_deterioration, plot_city_metric, plot_demand_impact
from roadies.visualization.kpis import calculate_kpis

st.set_page_config(page_title="High-Demand Analysis", page_icon="📈", layout="wide")
apply_theme()

df = load_dashboard_data()

if df.empty:
    st.warning("No data available.")
    st.stop()

filters = render_sidebar_filters(df)
filtered = filter_dataframe(
    df,
    cities=filters["cities"],
    min_surge=filters["surge_range"][0],
    max_surge=filters["surge_range"][1],
)

if filtered.empty or "is_high_demand" not in filtered.columns:
    st.info("No matching data for selected filters.")
    st.stop()

render_page_header(
    "HIGH-DEMAND OPERATIONS",
    "Demand pressure monitor",
    "Identify where rider experience deteriorates as demand pressure increases.",
)

# High-demand KPIs
render_section_header("DEMAND SIGNALS", "High-demand deterioration")
kpis = calculate_kpis(filtered)
render_kpi_grid(kpis.high_demand)

# Demand impact chart
render_section_header("COMPARISON", "High-demand impact", "Normal is shown in blue; high demand is shown in Road Orange.")
impact_df = filtered.groupby("is_high_demand").agg({
    "was_accepted": "mean",
    "rider_cancelled": "mean",
    "wait_time_minutes": "mean",
    "surge_multiplier": "mean",
}).reset_index()
impact_df["demand_period"] = impact_df["is_high_demand"].map({True: "high", False: "normal"})
impact_df.columns = ["is_high_demand", "acceptance_rate", "rider_cancel_rate", "avg_wait_time", "avg_surge", "demand_period"]
impact_df[["acceptance_rate", "rider_cancel_rate"]] *= 100

render_chart(plot_demand_impact(impact_df), height=360)

# City deterioration
render_section_header("CITY RESILIENCE", "City deterioration during high demand")
normal = filtered[~filtered["is_high_demand"]]
high = filtered[filtered["is_high_demand"]]

if len(normal) > 0 and len(high) > 0:
    city_normal = normal.groupby("city").agg({"rider_cancelled": "mean"}).reset_index()
    city_normal.columns = ["city", "normal_cancel"]
    city_high = high.groupby("city").agg({"rider_cancelled": "mean"}).reset_index()
    city_high.columns = ["city", "high_cancel"]

    deterior = city_normal.merge(city_high, on="city")
    deterior["cancel_change"] = (deterior["high_cancel"] - deterior["normal_cancel"]) * 100

    fig = plot_city_deterioration(deterior, metric="cancel_change")
    fig.update_layout(xaxis_title="City", yaxis_title="Cancellation change (pp)")
    render_chart(fig, height=340)

# Demand share by city
render_section_header("EXPOSURE", "High-demand share by city")
share_df = filtered.groupby(["city", "is_high_demand"]).size().reset_index(name="count")
total = share_df.groupby("city")["count"].transform("sum")
share_df["share"] = share_df["count"] / total * 100
hd_share = share_df[share_df["is_high_demand"] == True]

if not hd_share.empty:
    fig = plot_city_metric(hd_share[["city", "share"]], "share", title="High-Demand Share by City (%)")
    fig.update_layout(xaxis_title="City", yaxis_title="Share of rides (%)")
    render_chart(fig, height=330)
