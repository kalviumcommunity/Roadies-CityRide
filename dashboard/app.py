"""Roadies-CityRide Dashboard — Main entry point."""

from __future__ import annotations

from pathlib import Path
import sys

# Make imports work when Streamlit launches this file directly.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
for import_path in (PROJECT_ROOT, SRC_DIR):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))

import streamlit as st

from dashboard.theme import apply_theme
from roadies.config import load_settings
from roadies.ingestion.generator import generate_rides

st.set_page_config(
    page_title="Roadies-CityRide Analytics",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_theme()

st.markdown(
    """
    <section class="roadies-hero">
        <div class="roadies-eyebrow">Operations intelligence</div>
        <h1>Roadies-CityRide</h1>
        <p>Rider experience analytics for high-demand city-hours.</p>
    </section>
    """,
    unsafe_allow_html=True,
)

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


def generate_dataset(rows: int, seed: int) -> Path:
    """Generate the dashboard dataset from the Streamlit UI."""
    settings = load_settings()
    df = generate_rides(n_rows=rows, seed=seed)

    settings.synthetic_data_dir.mkdir(parents=True, exist_ok=True)
    settings.raw_data_dir.mkdir(parents=True, exist_ok=True)
    synthetic_path = settings.synthetic_data_dir / "rides.csv"
    raw_path = settings.raw_data_dir / "rides.csv"
    df.to_csv(synthetic_path, index=False)
    df.to_csv(raw_path, index=False)
    load_dashboard_data.clear()
    return raw_path


with st.sidebar:
    st.subheader("Dataset")
    settings = load_settings()
    data_path = settings.raw_data_dir / "rides.csv"
    default_rows = 50_000
    rows = st.number_input(
        "Number of rides",
        min_value=100,
        max_value=500_000,
        value=default_rows,
        step=10_000,
        help="Synthetic rides to generate for the dashboard.",
    )
    seed = st.number_input("Random seed", min_value=0, value=settings.random_seed, step=1)
    generate_clicked = st.button(
        "Generate / refresh dataset",
        type="primary",
        width="stretch",
    )

if generate_clicked or not data_path.exists():
    if not data_path.exists():
        st.info("No dataset found. Generate one here to start the dashboard.")

    with st.spinner(f"Generating {int(rows):,} rides…"):
        generated_path = generate_dataset(int(rows), int(seed))
    st.success(f"Dataset ready: {generated_path}")

df = load_dashboard_data()

if df.empty:
    st.warning("No data available. Use the Dataset controls in the sidebar to generate it.")
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
