"""City Analysis page — Compare cities across operational metrics."""

from __future__ import annotations

import streamlit as st

from dashboard.data_loader import filter_dataframe, load_dashboard_data
from dashboard.filters import render_sidebar_filters
from roadies.visualization import plot_city_heatmap, plot_city_metric, plot_demand_supply_relationship

st.set_page_config(page_title="City Analysis", page_icon="🏙️", layout="wide")

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

# City summary
st.header("City Performance Summary")
city_df = filtered.groupby("city").agg({
    "was_accepted": "mean",
    "rider_cancelled": "mean",
    "wait_time_minutes": "mean",
    "surge_multiplier": "mean",
}).reset_index()
city_df.columns = ["city", "acceptance_rate", "rider_cancel_rate", "avg_wait_time", "avg_surge"]
city_df[["acceptance_rate", "rider_cancel_rate"]] *= 100

st.dataframe(city_df.style.highlight_max(axis=0), use_container_width=True)

# Heatmap
st.header("Performance Heatmap")
fig = plot_city_heatmap(city_df)
st.plotly_chart(fig, use_container_width=True)

# Individual metrics
st.header("Metric Comparison")
metrics = ["acceptance_rate", "rider_cancel_rate", "avg_wait_time", "avg_surge"]
selected_metric = st.selectbox("Select Metric", options=metrics, format_func=lambda x: x.replace("_", " ").title())

fig = plot_city_metric(city_df, selected_metric)
st.plotly_chart(fig, use_container_width=True)

# Demand/supply relationship
st.header("Demand/Supply Relationship")
fig = plot_demand_supply_relationship(filtered.sample(min(500, len(filtered))))
st.plotly_chart(fig, use_container_width=True)
