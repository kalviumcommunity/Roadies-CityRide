"""Shared visual theme for the Roadies-CityRide Streamlit app."""

from __future__ import annotations

import streamlit as st

NAVY = "#040521"
BLUE = "#081D56"
SKY = "#62AAE5"
ORANGE = "#F59A2F"
WHITE = "#F8FAFC"
INK = "#14213D"
MUTED = "#94A3B8"
SURFACE = "#FFFFFF"
CANVAS = "#F4F7FB"
BORDER = "#1E2A4A"
SUCCESS = "#22C55E"
WARNING = ORANGE
DANGER = "#EF4444"


def apply_theme() -> None:
    """Apply the shared Roadies-CityRide UI theme."""
    st.markdown(
        f"""
        <style>
        :root {{
            --roadies-navy: {NAVY};
            --roadies-blue: {BLUE};
            --roadies-sky: {SKY};
            --roadies-orange: {ORANGE};
            --roadies-white: {WHITE};
            --roadies-ink: {INK};
            --roadies-muted: {MUTED};
            --roadies-surface: {SURFACE};
            --roadies-canvas: {CANVAS};
            --roadies-border: rgba(30, 42, 74, 0.14);
            --roadies-success: {SUCCESS};
            --roadies-danger: {DANGER};
        }}

        .stApp {{
            background: var(--roadies-canvas);
            color: var(--roadies-ink);
        }}

        [data-testid="stHeader"] {{
            background: transparent;
        }}

        section[data-testid="stSidebar"] {{
            min-width: 276px;
            max-width: 276px;
        }}

        [data-testid="stSidebar"] {{
            background: var(--roadies-navy);
            border-right: 1px solid rgba(98, 170, 229, 0.22);
        }}

        [data-testid="stSidebar"] * {{
            color: {WHITE};
        }}

        [data-testid="stSidebar"] [data-baseweb="select"] > div,
        [data-testid="stSidebar"] [data-baseweb="input"] > div {{
            background: rgba(255, 255, 255, 0.10);
            border-color: rgba(98, 170, 229, 0.45);
        }}

        [data-testid="stSidebar"] [data-testid="stMultiSelect"] span[data-baseweb="tag"] {{
            background: var(--roadies-blue);
            border: 1px solid rgba(98, 170, 229, 0.5);
        }}

        h1, h2, h3 {{
            color: var(--roadies-blue);
            letter-spacing: 0;
        }}

        h1 {{
            font-weight: 800;
        }}

        [data-testid="stMetric"] {{
            background: var(--roadies-surface);
            border: 1px solid var(--roadies-border);
            border-top: 4px solid var(--roadies-sky);
            border-radius: 10px;
            padding: 1rem 1.1rem;
            box-shadow: 0 8px 22px rgba(4, 5, 33, 0.06);
        }}

        [data-testid="stMetricLabel"] {{
            color: var(--roadies-muted);
        }}

        [data-testid="stMetricValue"] {{
            color: var(--roadies-blue);
        }}

        [data-testid="stAlert"] {{
            border-radius: 8px;
        }}

        .stButton > button {{
            background: var(--roadies-orange);
            color: var(--roadies-navy);
            border: 0;
            border-radius: 7px;
            font-weight: 700;
        }}

        .stButton > button:hover {{
            background: #FFB452;
            color: var(--roadies-navy);
        }}

        [data-testid="stDataFrame"] {{
            border: 1px solid var(--roadies-border);
            border-radius: 8px;
            overflow: hidden;
        }}

        .roadies-eyebrow {{
            color: var(--roadies-orange);
            font-size: 0.75rem;
            font-weight: 800;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            margin-bottom: 0.25rem;
        }}

        .roadies-hero {{
            background: linear-gradient(120deg, var(--roadies-navy), var(--roadies-blue));
            border-radius: 14px;
            color: {WHITE};
            padding: 1.5rem 1.75rem;
            margin-bottom: 1.25rem;
            box-shadow: 0 14px 30px rgba(4, 5, 33, 0.18);
        }}

        .roadies-hero h1,
        .roadies-hero p {{
            color: {WHITE};
            margin-bottom: 0.35rem;
        }}

        .roadies-hero p {{
            opacity: 0.82;
        }}

        .roadies-sidebar-brand {{
            display: flex;
            align-items: center;
            gap: 0.7rem;
            padding: 0.4rem 0.2rem 0.8rem;
            letter-spacing: 0.08em;
        }}

        .roadies-sidebar-brand strong,
        .roadies-sidebar-brand span {{ display: block; }}
        .roadies-sidebar-brand span {{ color: {SKY}; font-size: 0.66rem; letter-spacing: 0.2em; }}
        .roadies-mark {{
            display: grid; place-items: center; width: 2rem; height: 2rem;
            border-radius: 8px; background: {ORANGE}; color: {NAVY}; font-weight: 900;
        }}
        .roadies-sidebar-kicker {{ color: {MUTED}; font-size: 0.62rem; letter-spacing: 0.14em; margin: 0.2rem 0 1.4rem; }}
        .roadies-status-panel {{ border-top: 1px solid rgba(148, 163, 184, 0.22); margin-top: 2rem; padding-top: 1rem; color: {MUTED}; font-size: 0.62rem; letter-spacing: 0.06em; line-height: 2.25; }}
        .roadies-status-title {{ color: {ORANGE}; font-weight: 800; letter-spacing: 0.14em; margin-bottom: 0.3rem; }}
        .roadies-status-panel b {{ color: {WHITE}; font-weight: 700; float: right; }}
        .roadies-dot {{ display: inline-block; width: 7px; height: 7px; border-radius: 50%; margin-right: 0.4rem; }}
        .roadies-dot-good {{ background: {SUCCESS}; box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.16); }}
        .roadies-page-header {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; margin: 0.4rem 0 1.7rem; }}
        .roadies-page-header h1 {{ margin: 0.1rem 0 0.35rem; font-size: 2rem; }}
        .roadies-page-header p, .roadies-section-header p {{ color: {MUTED}; margin: 0; }}
        .roadies-system-pill {{ background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.28); border-radius: 999px; color: {SUCCESS}; padding: 0.45rem 0.75rem; font-size: 0.68rem; font-weight: 800; letter-spacing: 0.08em; white-space: nowrap; }}
        .roadies-section-header {{ margin: 1.6rem 0 0.7rem; }}
        .roadies-section-header h2 {{ margin: 0.1rem 0 0.25rem; font-size: 1.25rem; }}
        .roadies-stat-card {{ background: {SURFACE}; border: 1px solid var(--roadies-border); border-top: 3px solid {SKY}; border-radius: 12px; padding: 1rem 1.1rem; min-height: 108px; box-shadow: 0 8px 22px rgba(4, 5, 33, 0.05); }}
        .roadies-stat-label {{ color: {MUTED}; font-size: 0.68rem; font-weight: 800; letter-spacing: 0.1em; text-transform: uppercase; }}
        .roadies-stat-value {{ color: {BLUE}; font-size: 1.65rem; font-weight: 800; margin-top: 0.55rem; }}
        .roadies-stat-detail {{ color: {MUTED}; font-size: 0.75rem; margin-top: 0.2rem; }}
        .roadies-badge {{ border-radius: 999px; display: inline-block; font-size: 0.65rem; font-weight: 800; letter-spacing: 0.06em; padding: 0.22rem 0.5rem; }}
        .roadies-badge-normal {{ background: rgba(34, 197, 94, 0.13); color: #15803D; }}
        .roadies-badge-elevated {{ background: rgba(245, 154, 47, 0.16); color: #B45309; }}
        .roadies-badge-high {{ background: rgba(249, 115, 22, 0.16); color: #C2410C; }}
        .roadies-badge-critical {{ background: rgba(239, 68, 68, 0.14); color: #B91C1C; }}

        @media (max-width: 900px) {{
            .roadies-page-header {{ display: block; }}
            .roadies-system-pill {{ display: inline-block; margin-top: 0.8rem; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def apply_plotly_theme(fig):
    """Apply the dashboard palette to a Plotly figure and return it."""
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        font={"color": INK, "family": "Inter, Segoe UI, Arial, sans-serif"},
        title={"font": {"color": BLUE, "size": 18}},
        colorway=[SKY, ORANGE, DANGER, SUCCESS, MUTED],
        margin={"l": 24, "r": 24, "t": 56, "b": 24},
        hoverlabel={"bgcolor": NAVY, "font": {"color": "#FFFFFF"}},
        showlegend=True,
    )
    return fig
