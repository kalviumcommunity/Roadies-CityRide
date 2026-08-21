"""High-Demand Analysis page — Normal vs high-demand impact."""

from __future__ import annotations

import streamlit as st

from dashboard.data_loader import filter_dataframe, load_dashboard_data
from dashboard.filters import render_sidebar_filters
from roadies.visualization import plot_demand_impact, plot_city_deterioration
from roadies.visualization.kpis import build_kpi_cards, calculate_kpis

st.set_page_config(page_title="High-Demand Analysis", page_icon="📈", layout="wide")

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

# High-demand KPIs
st.header("High-Demand Deterioration KPIs")
kpis = calculate_kpis(filtered)
if kpis.high_demand:
    cols = st.columns(len(kpis.high_demand))
    for i, kpi in enumerate(kpis.high_demand):
        with cols[i]:
            delta_color = "inverse" if not kpi.higher_is_better else "normal"
            st.metric(
                label=kpi.label,
                value=kpi.formatted_value,
                delta=kpi.formatted_comparison,
                delta_color=delta_color,
            )

# Demand impact chart
st.header("Normal vs High Demand")
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

# City deterioration
st.header("City Deterioration During High Demand")
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
    st.plotly_chart(fig, use_container_width=True)

# Demand share by city
st.header("High-Demand Share by City")
share_df = filtered.groupby(["city", "is_high_demand"]).size().reset_index(name="count")
total = share_df.groupby("city")["count"].transform("sum")
share_df["share"] = share_df["count"] / total * 100
hd_share = share_df[share_df["is_high_demand"] == True]

if not hd_share.empty:
    fig = plot_city_metric(hd_share[["city", "share"]], "share", title="High-Demand Share by City (%)")
    st.plotly_chart(fig, use_container_width=True)
