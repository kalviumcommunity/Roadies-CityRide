"""City Analysis page — Compare cities across operational metrics."""

from __future__ import annotations

import streamlit as st

from dashboard.components import render_chart, render_page_header, render_section_header
from dashboard.data_loader import filter_dataframe, load_dashboard_data
from dashboard.filters import render_sidebar_filters
from dashboard.theme import apply_theme
from roadies.visualization import plot_city_heatmap, plot_city_metric, plot_demand_supply_relationship

st.set_page_config(page_title="City Analysis", page_icon="🏙️", layout="wide")
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
    "CITY INTELLIGENCE",
    "Market health comparison",
    "Compare operational health across Roadies CityRide markets.",
)

# City summary
render_section_header("MARKET SCORECARD", "City performance summary")
city_df = filtered.groupby("city").agg({
    "was_accepted": "mean",
    "rider_cancelled": "mean",
    "wait_time_minutes": "mean",
    "surge_multiplier": "mean",
}).reset_index()
city_df.columns = ["city", "acceptance_rate", "rider_cancel_rate", "avg_wait_time", "avg_surge"]
city_df[["acceptance_rate", "rider_cancel_rate"]] *= 100

display_df = city_df.rename(columns={
    "city": "City", "acceptance_rate": "Acceptance Rate", "rider_cancel_rate": "Rider Cancel Rate",
    "avg_wait_time": "Avg Wait", "avg_surge": "Avg Surge",
})
display_df["Acceptance Rate"] = display_df["Acceptance Rate"].map(lambda value: f"{value:.1f}%")
display_df["Rider Cancel Rate"] = display_df["Rider Cancel Rate"].map(lambda value: f"{value:.1f}%")
display_df["Avg Wait"] = display_df["Avg Wait"].map(lambda value: f"{value:.2f} min")
display_df["Avg Surge"] = display_df["Avg Surge"].map(lambda value: f"{value:.2f}x")
st.dataframe(display_df, use_container_width=True, hide_index=True)

# Heatmap
render_section_header("PERFORMANCE MAP", "Operational health heatmap")
render_chart(plot_city_heatmap(city_df), height=360)

# Individual metrics
render_section_header("METRIC EXPLORER", "Compare one operating signal")
metrics = ["acceptance_rate", "rider_cancel_rate", "avg_wait_time", "avg_surge"]
selected_metric = st.selectbox("Select Metric", options=metrics, format_func=lambda x: x.replace("_", " ").title())

render_chart(plot_city_metric(city_df, selected_metric), height=330)

# Demand/supply relationship
render_section_header("PRESSURE SIGNAL", "Demand versus supply")
render_chart(plot_demand_supply_relationship(filtered.sample(min(500, len(filtered)), random_state=42)), height=360)
