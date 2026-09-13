"""Risk & Anomalies page — Operational risk and anomaly indicators."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.components import (
    friendly_metric,
    render_chart,
    render_metric_cards,
    render_page_header,
    render_section_header,
)
from dashboard.data_loader import filter_dataframe, load_dashboard_data
from dashboard.filters import render_sidebar_filters
from dashboard.theme import apply_theme
from roadies.analysis.anomaly import classify_risk, detect_anomalies

st.set_page_config(page_title="Risk & Anomalies", page_icon="⚠️", layout="wide")
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

# Anomaly detection
render_page_header(
    "RISK & ANOMALIES",
    "Operational risk monitor",
    "Detect abnormal demand, supply, and rider-experience patterns.",
)

anomalies = detect_anomalies(filtered)
high_surge_count = int((filtered["surge_multiplier"] > 2.0).sum()) if "surge_multiplier" in filtered else 0
long_wait_count = int((filtered["wait_time_minutes"] > 15).sum()) if "wait_time_minutes" in filtered else 0
cancel_rate = filtered["rider_cancelled"].mean() * 100 if "rider_cancelled" in filtered else 0.0

render_section_header("ANOMALY SUMMARY", "Signals requiring attention")
render_metric_cards([
    ("Anomalous Periods", f"{len(anomalies):,}", "Detected by the analysis engine"),
    ("High Surge Rides", f"{high_surge_count:,}", "Surge multiplier above 2.0x"),
    ("Long Wait Rides", f"{long_wait_count:,}", "Wait time above 15 minutes"),
    ("Overall Cancel Rate", f"{cancel_rate:.1f}%", "Rider cancellations in selection"),
])

anomaly_df = pd.DataFrame([anomaly.__dict__ for anomaly in anomalies])
if not anomaly_df.empty:
    render_section_header("ANOMALY LOG", "Most significant detected periods")
    anomaly_display = anomaly_df.rename(columns={
        "metric": "Metric", "value": "Observed Value", "baseline": "Baseline",
        "deviation": "Deviation", "relative_deviation": "Relative Deviation",
        "anomaly_type": "Type", "city": "City", "severity": "Severity",
    })
    anomaly_display["Metric"] = anomaly_display["Metric"].map(friendly_metric)
    for column in ["Observed Value", "Baseline", "Deviation"]:
        anomaly_display[column] = anomaly_display[column].map(lambda value: f"{value:.2f}")
    anomaly_display["Relative Deviation"] = anomaly_display["Relative Deviation"].map(lambda value: f"{value * 100:.1f}%")
    anomaly_display["Severity"] = anomaly_display["Severity"].str.upper()
    st.dataframe(anomaly_display.head(20), width="stretch", hide_index=True)

# Risk classification
render_section_header("CITY RISK MATRIX", "Operational risk by city")
risk_df = classify_risk(filtered)

if not risk_df.empty:
    if "risk_level" in risk_df.columns:
        risk_counts = risk_df.groupby(["city", "risk_level"]).size().reset_index(name="count")
        risk_matrix = risk_counts.pivot(index="city", columns="risk_level", values="count").fillna(0).astype(int)
        for level in ["normal", "elevated", "high", "critical"]:
            if level not in risk_matrix:
                risk_matrix[level] = 0
        risk_matrix = risk_matrix[["normal", "elevated", "high", "critical"]].reset_index()
        risk_matrix.columns = ["City", "Normal", "Elevated", "High", "Critical"]
        st.dataframe(risk_matrix, width="stretch", hide_index=True)

        render_section_header("DISTRIBUTION", "Risk level distribution")
        chart_df = risk_counts.copy()
        chart_df["risk_level"] = chart_df["risk_level"].str.title()
        fig = px.bar(
            chart_df,
            x="count",
            y="city",
            color="risk_level",
            orientation="h",
            barmode="stack",
            category_orders={"risk_level": ["Normal", "Elevated", "High", "Critical"]},
            color_discrete_map={"Normal": "#22C55E", "Elevated": "#F59A2F", "High": "#F97316", "Critical": "#EF4444"},
            labels={"count": "Observations", "city": "City", "risk_level": "Risk Level"},
        )
        render_chart(fig, height=380)

# City risk ranking
render_section_header("PRIORITIZATION", "City risk ranking")
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

    city_display = city_risk.rename(columns={
        "city": "City", "avg_surge": "Avg Surge", "cancel_rate": "Cancel Rate",
        "avg_wait": "Avg Wait", "risk_score": "Risk Score",
    })
    city_display["Avg Surge"] = city_display["Avg Surge"].map(lambda value: f"{value:.2f}x")
    city_display["Cancel Rate"] = city_display["Cancel Rate"].map(lambda value: f"{value:.1f}%")
    city_display["Avg Wait"] = city_display["Avg Wait"].map(lambda value: f"{value:.2f} min")
    city_display["Risk Score"] = city_display["Risk Score"].map(lambda value: f"{value:.2f}")
    city_display.insert(0, "Rank", range(1, len(city_display) + 1))
    st.dataframe(city_display, width="stretch", hide_index=True)
