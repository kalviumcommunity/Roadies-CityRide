"""Data loading helpers for the Streamlit dashboard."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from roadies.features.acceptance import engineer_acceptance_features
from roadies.features.cancellation import engineer_cancellation_features
from roadies.features.demand_period import classify_high_demand
from roadies.features.demand_supply import engineer_demand_supply_features
from roadies.features.experience import engineer_experience_features
from roadies.features.surge import engineer_surge_features
from roadies.ingestion.loaders import load_csv


@st.cache_data
def load_dashboard_data(csv_path: str = "data/raw/rides.csv") -> pd.DataFrame:
    """Load and engineer features for the dashboard."""
    p = Path(csv_path)
    if not p.exists():
        return pd.DataFrame()

    df = load_csv(p)
    df, _ = engineer_demand_supply_features(df)
    df, _ = engineer_surge_features(df)
    df, _ = engineer_acceptance_features(df)
    df, _ = engineer_cancellation_features(df)
    df, _ = engineer_experience_features(df)
    df, _ = classify_high_demand(df)
    return df


def filter_dataframe(
    df: pd.DataFrame,
    cities: list[str] | None = None,
    high_demand_only: bool | None = None,
    demand_category: str | None = None,
    min_surge: float | None = None,
    max_surge: float | None = None,
) -> pd.DataFrame:
    """Apply dashboard filters to the dataframe."""
    if df.empty:
        return df

    if cities:
        df = df[df["city"].isin(cities)]

    if high_demand_only is not None and "is_high_demand" in df.columns:
        df = df[df["is_high_demand"] == high_demand_only]

    if demand_category and "demand_category" in df.columns:
        df = df[df["demand_category"] == demand_category]

    if min_surge is not None and "surge_multiplier" in df.columns:
        df = df[df["surge_multiplier"] >= min_surge]

    if max_surge is not None and "surge_multiplier" in df.columns:
        df = df[df["surge_multiplier"] <= max_surge]

    return df
