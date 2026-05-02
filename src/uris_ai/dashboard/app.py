"""
URIS-AI Streamlit Dashboard Application.

Main entry point for the Streamlit dashboard.

Requirements: 6.1, 6.2, 6.5, 6.6, 10.1, 10.3
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

import streamlit as st

# ---------------------------------------------------------------------------
# Page configuration – MUST be the first Streamlit call
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="URIS-AI – Sistem Risiko Urban",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/uris-ai",
        "Report a bug": "https://github.com/uris-ai/issues",
        "About": (
            "**URIS-AI** – Urban Risk Intelligence System for Flood-Aware Mobility "
            "and Public Service Optimization\n\n"
            "_From Data to Decision for Smarter Urban Resilience_"
        ),
    },
)

# ---------------------------------------------------------------------------
# Responsive CSS injection (Req 6.5 – min 360px width)
# ---------------------------------------------------------------------------

RESPONSIVE_CSS = """
<style>
/* Ensure minimum 360px width for mobile compatibility */
.main .block-container {
    min-width: 360px;
    padding-top: 1rem;
    padding-bottom: 1rem;
    padding-left: 1rem;
    padding-right: 1rem;
}

/* Responsive metric cards */
[data-testid="metric-container"] {
    background: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 8px;
    padding: 12px;
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    min-width: 240px;
}

/* Mobile: stack columns vertically on small screens */
@media (max-width: 640px) {
    [data-testid="column"] {
        width: 100% !important;
        flex: 1 1 100% !important;
    }
    .main .block-container {
        padding-left: 0.5rem;
        padding-right: 0.5rem;
    }
}

/* Improve button appearance */
.stButton > button {
    border-radius: 6px;
    font-weight: 500;
}

/* Risk badge styling */
.risk-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 16px;
    font-weight: bold;
    font-size: 14px;
    color: white;
}

/* Scrollable recommendation list */
.rec-scroll {
    max-height: 400px;
    overflow-y: auto;
    padding-right: 4px;
}

/* Hide Streamlit branding on mobile */
@media (max-width: 480px) {
    footer { display: none; }
    #MainMenu { display: none; }
}

/* Map container height reduction on mobile */
@media (max-width: 640px) {
    iframe {
        max-height: 300px !important;
    }
}

/* Font size adjustments for small screens */
@media (max-width: 480px) {
    .main .block-container {
        font-size: 14px;
    }
    h1 { font-size: 1.4rem !important; }
    h2 { font-size: 1.2rem !important; }
    h3 { font-size: 1.0rem !important; }
    [data-testid="metric-container"] {
        padding: 8px;
    }
    .risk-badge {
        font-size: 12px;
        padding: 3px 8px;
    }
}
</style>
"""

st.markdown(RESPONSIVE_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Imports (after page config)
# ---------------------------------------------------------------------------

from uris_ai.dashboard.api_client import (  # noqa: E402
    APIClient,
    DEMO_RECOMMENDATIONS,
    DEMO_REGIONS,
    DEMO_TREND,
)
from uris_ai.dashboard.components.filters import (  # noqa: E402
    apply_risk_category_filter,
    render_filter_summary,
    render_filters,
)
from uris_ai.dashboard.components.map_visualizer import (  # noqa: E402
    render_map,
    render_map_summary,
)
from uris_ai.dashboard.components.recommendation_panel import (  # noqa: E402
    render_recommendation_panel,
)
from uris_ai.dashboard.components.risk_dashboard import render_risk_dashboard  # noqa: E402
from uris_ai.dashboard.components.user_interface import (  # noqa: E402
    can_access_page,
    get_current_role,
    get_current_user,
    is_authenticated,
    render_access_denied,
    render_login_form,
    render_user_info,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# API client initialisation
# ---------------------------------------------------------------------------

API_BASE_URL = os.environ.get("URIS_AI_API_URL", "http://localhost:8000")


@st.cache_resource
def get_api_client() -> APIClient:
    """Return a cached APIClient instance."""
    return APIClient(base_url=API_BASE_URL)


# ---------------------------------------------------------------------------
# Data loading helpers (with demo fallback)
# ---------------------------------------------------------------------------


@st.cache_data(ttl=60)  # cache for 60 seconds (Req 6.2 – update within 3s on interaction)
def load_all_regions(token: Optional[str] = None) -> List[Dict[str, Any]]:
    """Load risk data for all regions, falling back to demo data."""
    client = get_api_client()
    if token:
        client.set_token(token)
    result = client.get_all_regions_risk()
    if result and "regions" in result:
        return result["regions"]
    logger.info("Using demo region data (backend unavailable).")
    return DEMO_REGIONS


@st.cache_data(ttl=60)
def load_region_risk(region_id: int, token: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Load risk data for a single region."""
    client = get_api_client()
    if token:
        client.set_token(token)
    result = client.get_region_risk(region_id)
    if result:
        return result
    # Fall back to demo data
    return next((r for r in DEMO_REGIONS if r.get("region_id") == region_id), None)


@st.cache_data(ttl=60)
def load_risk_trend(
    region_id: int, hours: int = 24, token: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Load risk trend for a region."""
    client = get_api_client()
    if token:
        client.set_token(token)
    result = client.get_risk_trend(region_id, hours=hours)
    if result and "trend" in result:
        return result["trend"]
    return DEMO_TREND


@st.cache_data(ttl=60)
def load_recommendations(
    region_id: int, token: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Load recommendations for a region."""
    client = get_api_client()
    if token:
        client.set_token(token)
    result = client.get_recommendations(region_id)
    if result and "recommendations" in result:
        return result["recommendations"]
    return [r for r in DEMO_RECOMMENDATIONS if r.get("region_id") == region_id]


# ---------------------------------------------------------------------------
# Page renderers
# ---------------------------------------------------------------------------


def render_risk_map_page(filters: Dict[str, Any]) -> None:
    """
    Render the main risk map page.

    Requirements: 6.1, 6.2, 4.2
    """
    st.header("🗺️ Peta Risiko Urban")
    render_filter_summary(filters)

    token = st.session_state.get("token")
    all_regions = load_all_regions(token=token)

    # Apply category filter
    filtered_regions = apply_risk_category_filter(
        all_regions, filters.get("risk_categories", [])
    )

    # Summary metrics
    render_map_summary(filtered_regions)
    st.markdown("---")

    # Map + detail panel layout
    selected_id = filters.get("selected_region_id") or st.session_state.get(
        "selected_region_id"
    )

    if selected_id:
        # Two-column layout: map | detail
        col_map, col_detail = st.columns([3, 2])
        with col_map:
            render_map(filtered_regions, height=480, key="main_risk_map")
        with col_detail:
            region_data = load_region_risk(selected_id, token=token)
            trend_data = load_risk_trend(
                selected_id, hours=filters.get("time_range_hours", 24), token=token
            )
            render_risk_dashboard(region_data or {}, trend_data=trend_data)
    else:
        # Full-width map
        render_map(filtered_regions, height=520, key="main_risk_map")
        st.info(
            "💡 Pilih wilayah pada peta atau gunakan dropdown di atas untuk melihat detail risiko."
        )


def render_region_detail_page(filters: Dict[str, Any]) -> None:
    """
    Render the region detail page.

    Requirements: 6.6
    """
    st.header("📍 Detail Wilayah")
    render_filter_summary(filters)

    token = st.session_state.get("token")
    all_regions = load_all_regions(token=token)
    selected_id = filters.get("selected_region_id") or st.session_state.get(
        "selected_region_id"
    )

    if not selected_id:
        st.info("Pilih wilayah dari sidebar atau halaman Peta Risiko untuk melihat detail.")
        # Show region list as quick-select
        st.markdown("### Daftar Wilayah")
        cols = st.columns(3)
        for i, region in enumerate(all_regions):
            with cols[i % 3]:
                name = region.get("region_name", f"Wilayah {region.get('region_id')}")
                urs = float(region.get("urban_risk_score", 0))
                cat = region.get("risk_category", "RENDAH")
                if st.button(f"{name}\nURS: {urs:.1f} ({cat})", key=f"region_btn_{i}"):
                    st.session_state["selected_region_id"] = region.get("region_id")
                    st.rerun()
        return

    region_data = load_region_risk(selected_id, token=token)
    trend_data = load_risk_trend(
        selected_id, hours=filters.get("time_range_hours", 24), token=token
    )

    render_risk_dashboard(region_data or {}, trend_data=trend_data)


def render_recommendations_page(filters: Dict[str, Any]) -> None:
    """
    Render the recommendations page.

    Requirements: 6.6, 5.1
    """
    st.header("💡 Rekomendasi Tindakan")
    render_filter_summary(filters)

    token = st.session_state.get("token")
    selected_id = filters.get("selected_region_id") or st.session_state.get(
        "selected_region_id"
    )

    client = get_api_client()
    if token:
        client.set_token(token)

    if selected_id:
        recs = load_recommendations(selected_id, token=token)
        render_recommendation_panel(
            recommendations=recs,
            api_client=client,
            show_route_finder=True,
        )
    else:
        st.info("Pilih wilayah untuk melihat rekomendasi spesifik.")
        # Show route finder even without region selection
        from uris_ai.dashboard.components.recommendation_panel import render_route_finder
        render_route_finder(client)


def render_analytics_page(filters: Dict[str, Any]) -> None:
    """
    Render the analytics page (government role only).

    Requirements: 4.4
    """
    st.header("📊 Analitik & Tren")
    render_filter_summary(filters)

    token = st.session_state.get("token")
    all_regions = load_all_regions(token=token)

    if not all_regions:
        st.warning("Data analitik tidak tersedia saat ini.")
        return

    import plotly.graph_objects as go

    # URS distribution bar chart
    st.markdown("### Distribusi Urban Risk Score")
    names = [r.get("region_name", f"W{r.get('region_id')}") for r in all_regions]
    scores = [float(r.get("urban_risk_score", 0)) for r in all_regions]
    cats = [r.get("risk_category", "RENDAH") for r in all_regions]

    color_map = {
        "RENDAH": "#2ecc71",
        "SEDANG": "#f39c12",
        "TINGGI": "#e74c3c",
        "KRITIS": "#8e44ad",
    }
    bar_colors = [color_map.get(c, "#999") for c in cats]

    fig = go.Figure(
        go.Bar(
            x=names,
            y=scores,
            marker_color=bar_colors,
            hovertemplate="<b>%{x}</b><br>URS: %{y:.1f}<extra></extra>",
        )
    )
    fig.update_layout(
        xaxis_title="Wilayah",
        yaxis_title="Urban Risk Score",
        yaxis={"range": [0, 100]},
        height=350,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"t": 20, "b": 60},
    )
    fig.add_hline(y=70, line_dash="dash", line_color="#e74c3c", annotation_text="Ambang Kritis")
    st.plotly_chart(fig, use_container_width=True)

    # Component breakdown table
    st.markdown("### Rincian Komponen Risiko per Wilayah")
    import pandas as pd

    df = pd.DataFrame(
        [
            {
                "Wilayah": r.get("region_name", f"W{r.get('region_id')}"),
                "URS": round(float(r.get("urban_risk_score", 0)), 1),
                "Risiko Banjir": round(float(r.get("flood_risk", 0)), 1),
                "Dampak Lalu Lintas": round(float(r.get("traffic_impact", 0)), 1),
                "Aksesibilitas Layanan": round(float(r.get("service_access", 0)), 1),
                "Kategori": r.get("risk_category", "RENDAH"),
            }
            for r in all_regions
        ]
    )
    st.dataframe(df, use_container_width=True, hide_index=True)


def render_login_page() -> None:
    """Render the login page."""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        client = get_api_client()
        logged_in = render_login_form(client)
        if logged_in:
            st.rerun()

        st.markdown("---")
        st.markdown(
            """
            **Akun Demo:**
            | Username | Password | Peran |
            |----------|----------|-------|
            | `admin` | `admin123` | Pemerintah |
            | `pengelola` | `pengelola123` | Pengelola Fasilitas |
            | `publik` | `publik123` | Masyarakat Umum |
            """,
            unsafe_allow_html=False,
        )
        st.caption("Atau gunakan peta risiko tanpa login (akses terbatas).")


# ---------------------------------------------------------------------------
# Navigation pages definition
# ---------------------------------------------------------------------------

PAGES = {
    "Peta Risiko": render_risk_map_page,
    "Detail Wilayah": render_region_detail_page,
    "Rekomendasi": render_recommendations_page,
    "Analitik": render_analytics_page,
    "Navigasi Rute": None,  # handled inline in recommendation panel
}


# ---------------------------------------------------------------------------
# Main application
# ---------------------------------------------------------------------------


def main() -> None:
    """Main Streamlit application entry point."""
    # ------------------------------------------------------------------
    # Sidebar: branding + navigation + user info + filters
    # ------------------------------------------------------------------
    with st.sidebar:
        st.markdown(
            """
            <div style="text-align:center; padding: 8px 0;">
                <span style="font-size:36px;">🌊</span>
                <h2 style="margin:4px 0 0 0; font-size:20px;">URIS-AI</h2>
                <p style="font-size:12px; color:#888; margin:2px 0;">
                    Urban Risk Intelligence System
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # User info / logout
        render_user_info()

        st.markdown("---")
        st.markdown("### 📌 Navigasi")

        # Build page list based on role
        role = get_current_role()
        from uris_ai.dashboard.components.user_interface import ROLES

        if role:
            allowed = ROLES.get(role, {}).get("allowed_pages", ["Peta Risiko"])
        else:
            allowed = ["Peta Risiko"]

        available_pages = [p for p in PAGES.keys() if p in allowed and p != "Navigasi Rute"]

        if not available_pages:
            available_pages = ["Peta Risiko"]

        selected_page = st.radio(
            "Halaman",
            options=available_pages,
            label_visibility="collapsed",
            key="nav_radio",
        )

        # Login / logout button
        st.markdown("---")
        if not is_authenticated():
            if st.button("🔐 Masuk", use_container_width=True, key="sidebar_login_btn"):
                st.session_state["show_login"] = True
                st.rerun()
        else:
            user = get_current_user()
            if user:
                st.caption(f"Masuk sebagai: **{user.get('username', '')}**")

    # ------------------------------------------------------------------
    # Filters (rendered in sidebar, returns current values)
    # ------------------------------------------------------------------
    token = st.session_state.get("token")
    all_regions_for_filter = load_all_regions(token=token)
    filters = render_filters(regions=all_regions_for_filter)

    # ------------------------------------------------------------------
    # Main content area
    # ------------------------------------------------------------------

    # Show login page if requested
    if st.session_state.get("show_login") and not is_authenticated():
        render_login_page()
        return

    # Clear login flag once authenticated
    if is_authenticated() and st.session_state.get("show_login"):
        st.session_state["show_login"] = False

    # Check page access
    if not can_access_page(selected_page):
        render_access_denied(selected_page)
        return

    # Render selected page
    page_renderer = PAGES.get(selected_page)
    if page_renderer:
        page_renderer(filters)
    else:
        st.info(f"Halaman '{selected_page}' sedang dalam pengembangan.")

    # ------------------------------------------------------------------
    # Footer
    # ------------------------------------------------------------------
    st.markdown("---")
    st.markdown(
        "<div style='text-align:center; color:#888; font-size:12px;'>"
        "© 2024 URIS-AI Team · "
        "<em>From Data to Decision for Smarter Urban Resilience</em>"
        "</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
