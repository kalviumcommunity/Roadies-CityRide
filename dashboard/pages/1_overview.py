"""Overview page — Core KPIs and top findings."""

from __future__ import annotations

import streamlit as st

from dashboard.data_loader import filter_dataframe, load_dashboard_data
from dashboard.filters import render_sidebar_filters
from roadies.visualization.kpis import build_kpi_cards, calculate_kpis
from roadies.visualization import plot_demand_impact, plot_city_metric

st.set_page_config(page_title="Overview", page_icon="📊", layout="wide")

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

# KPIs
st.header("Core KPIs")
kpis = calculate_kpis(filtered)
cols = st.columns(len(kpis.overall))
for i, kpi in enumerate(kpis.overall):
    with cols[i]:
        st.metric(
            label=kpi.label,
            value=kpi.formatted_value,
            delta=kpi.formatted_comparison if kpi.formatted_comparison else None,
        )

# High-demand impact
st.header("High-Demand Impact")
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

    fig = plot_demand_impact(impact_df)
    st.plotly_chart(fig, use_container_width=True)

# City comparison
st.header("City Comparison")
city_df = filtered.groupby("city").agg({
    "rider_cancelled": "mean",
}).reset_index()
city_df.columns = ["city", "rider_cancel_rate"]
city_df["rider_cancel_rate"] *= 100

fig = plot_city_metric(city_df, "rider_cancel_rate", title="Rider Cancel Rate by City")
st.plotly_chart(fig, use_container_width=True)
