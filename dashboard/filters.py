"""Sidebar filters for the Streamlit dashboard."""

from __future__ import annotations

import pandas as pd
import streamlit as st


def render_sidebar_filters(df: pd.DataFrame) -> dict:
    """Render sidebar filters and return selected values."""
    st.sidebar.header("Filters")

    # City filter
    cities = sorted(df["city"].unique()) if not df.empty else []
    selected_cities = st.sidebar.multiselect(
        "Cities",
        options=cities,
        default=cities,
    )

    # Demand period filter
    demand_options = ["All", "Normal", "High"]
    demand_choice = st.sidebar.selectbox("Demand Period", options=demand_options)

    # Surge range
    if "surge_multiplier" in df.columns and not df.empty:
        min_surge = float(df["surge_multiplier"].min())
        max_surge = float(df["surge_multiplier"].max())
        surge_range = st.sidebar.slider(
            "Surge Range",
            min_value=min_surge,
            max_value=max_surge,
            value=(min_surge, max_surge),
        )
    else:
        surge_range = (1.0, 3.0)

    return {
        "cities": selected_cities,
        "demand_choice": demand_choice,
        "surge_range": surge_range,
    }
