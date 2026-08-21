"""Risk & Anomalies page — Operational risk and anomaly indicators."""

from __future__ import annotations

import numpy as np
import streamlit as st

from dashboard.data_loader import filter_dataframe, load_dashboard_data
from dashboard.filters import render_sidebar_filters
from roadies.analysis.anomaly import classify_risk, detect_anomalies

st.set_page_config(page_title="Risk & Anomalies", page_icon="⚠️", layout="wide")

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

# Anomaly detection
st.header("Anomaly Detection")
anomalies = detect_anomalies(filtered)
st.write(f"Detected **{len(anomalies)}** anomalous periods")

if not anomalies.empty:
    st.dataframe(anomalies.head(20), use_container_width=True)

# Risk classification
st.header("Operational Risk by City")
risk_df = classify_risk(filtered)

if not risk_df.empty:
    if "risk_level" in risk_df.columns:
        risk_counts = risk_df.groupby(["city", "risk_level"]).size().reset_index(name="count")
        st.dataframe(risk_counts, use_container_width=True)

        # Risk distribution
        st.subheader("Risk Level Distribution")
        for city in risk_df["city"].unique():
            city_risk = risk_df[risk_df["city"] == city]
            if "risk_level" in city_risk.columns:
                risk_counts = city_risk["risk_level"].value_counts()
                st.write(f"**{city}**: {dict(risk_counts)}")

# High-risk indicators
st.header("High-Risk Indicators")
if "surge_multiplier" in filtered.columns:
    high_surge = filtered[filtered["surge_multiplier"] > 2.0]
    st.metric("High Surge Rides (>2×)", f"{len(high_surge):,}")

if "rider_cancelled" in filtered.columns:
    cancel_rate = filtered["rider_cancelled"].mean() * 100
    st.metric("Overall Cancel Rate", f"{cancel_rate:.1f}%")

if "wait_time_minutes" in filtered.columns:
    long_wait = filtered[filtered["wait_time_minutes"] > 15]
    st.metric("Long Wait Rides (>15 min)", f"{len(long_wait):,}")

# City risk ranking
st.header("City Risk Ranking")
if "city" in filtered.columns:
    city_risk = filtered.groupby("city").agg({
        "surge_multiplier": "mean",
        "rider_cancelled": "mean",
        "wait_time_minutes": "mean",
    }).reset_index()
    city_risk.columns = ["city", "avg_surge", "cancel_rate", "avg_wait"]
    city_risk["cancel_rate"] *= 100
    city_risk["risk_score"] = city_risk["avg_surge"] + city_risk["cancel_rate"] / 10 + city_risk["avg_wait"] / 10
    city_risk = city_risk.sort_values("risk_score", ascending=False)

    st.dataframe(city_risk, use_container_width=True)
