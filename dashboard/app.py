"""Roadies-CityRide Dashboard — Main entry point."""

from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="Roadies-CityRide Analytics",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Roadies-CityRide Analytics Dashboard")

st.markdown("""
Welcome to the **Roadies-CityRide Analytics Dashboard**.

This dashboard answers the core question:

> **Which city-level behaviours consistently degrade rider experience during high-demand periods?**

Use the sidebar navigation to explore:

- **Overview** — Core KPIs and top findings
- **City Analysis** — Compare cities across operational metrics
- **High-Demand Analysis** — Normal vs high-demand impact
- **Risk & Anomalies** — Operational risk and anomaly indicators
""")

from dashboard.data_loader import load_dashboard_data

df = load_dashboard_data()

if df.empty:
    st.warning("No data found. Run `uv run python -m roadies.ingestion.generator` first to generate the dataset.")
    st.stop()

st.success(f"Dataset loaded: {len(df):,} rides across {df['city'].nunique()} cities")

# Quick overview
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Rides", f"{len(df):,}")
col2.metric("Cities", df["city"].nunique())
col3.metric("Acceptance Rate", f"{df['was_accepted'].mean() * 100:.1f}%")
col4.metric("Rider Cancel Rate", f"{df['rider_cancelled'].mean() * 100:.1f}%")

st.divider()
st.caption("Navigate using the sidebar to explore detailed analysis.")
