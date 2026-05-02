"""
Recommendation Panel component for URIS-AI dashboard.

Displays recommendations with urgency levels, safe routes on map,
and alternative facilities.

Requirements: 6.6, 5.1
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import folium
import streamlit as st

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Urgency styling
# ---------------------------------------------------------------------------

URGENCY_CONFIG: Dict[str, Dict[str, str]] = {
    "Segera": {
        "color": "#e74c3c",
        "bg": "#fdf2f2",
        "border": "#e74c3c",
        "icon": "🚨",
        "description": "Tindakan diperlukan dalam 1 jam",
    },
    "Waspada": {
        "color": "#f39c12",
        "bg": "#fef9f0",
        "border": "#f39c12",
        "icon": "⚠️",
        "description": "Tindakan diperlukan dalam 1–6 jam",
    },
    "Siaga": {
        "color": "#3498db",
        "bg": "#f0f7fd",
        "border": "#3498db",
        "icon": "ℹ️",
        "description": "Tindakan diperlukan dalam 6–24 jam",
    },
}

TYPE_ICONS: Dict[str, str] = {
    "alert": "🔔",
    "route": "🗺️",
    "service": "🏥",
}

TYPE_LABELS: Dict[str, str] = {
    "alert": "Peringatan",
    "route": "Rute Alternatif",
    "service": "Fasilitas Alternatif",
}


# ---------------------------------------------------------------------------
# Single recommendation card
# ---------------------------------------------------------------------------


def _render_recommendation_card(rec: Dict[str, Any]) -> None:
    """Render a single recommendation as a styled card."""
    urgency = rec.get("urgency", "Siaga")
    rec_type = rec.get("type", "alert")
    description = rec.get("description", "")
    expires_at = rec.get("expires_at")

    cfg = URGENCY_CONFIG.get(urgency, URGENCY_CONFIG["Siaga"])
    type_icon = TYPE_ICONS.get(rec_type, "📋")
    type_label = TYPE_LABELS.get(rec_type, rec_type.capitalize())

    expires_html = ""
    if expires_at:
        ts = str(expires_at)[:19].replace("T", " ")
        expires_html = f'<div style="font-size:11px;color:#888;margin-top:4px;">Berlaku hingga: {ts}</div>'

    st.markdown(
        f"""
        <div style="
            background:{cfg['bg']};
            border-left:4px solid {cfg['border']};
            border-radius:6px;
            padding:12px 16px;
            margin-bottom:10px;
        ">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <span style="font-size:13px;color:#555;">
                    {type_icon} {type_label}
                </span>
                <span style="
                    background:{cfg['color']};
                    color:white;
                    padding:2px 8px;
                    border-radius:12px;
                    font-size:12px;
                    font-weight:bold;
                ">
                    {cfg['icon']} {urgency}
                </span>
            </div>
            <div style="margin-top:8px;font-size:14px;color:#2c3e50;line-height:1.5;">
                {description}
            </div>
            {expires_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Safe route map
# ---------------------------------------------------------------------------


def render_safe_route_map(
    route_result: Dict[str, Any],
    height: int = 350,
    key: str = "route_map",
) -> None:
    """
    Render a Folium map showing the safe route result.

    Args:
        route_result: SafeRouteResponse dict from the API.
        height: Map height in pixels.
        key: Unique Streamlit widget key.
    """
    try:
        from streamlit_folium import st_folium  # type: ignore[import]
    except ImportError:
        st.error("Paket `streamlit-folium` belum terpasang.")
        return

    origin = route_result.get("origin", {})
    destination = route_result.get("destination", {})
    is_safe = route_result.get("is_safe", False)
    avoided = route_result.get("avoided_regions", [])

    if not origin or not destination:
        st.warning("Data rute tidak lengkap.")
        return

    o_lat = origin.get("latitude", -6.2088)
    o_lon = origin.get("longitude", 106.8456)
    d_lat = destination.get("latitude", -6.2088)
    d_lon = destination.get("longitude", 106.8456)

    center_lat = (o_lat + d_lat) / 2
    center_lon = (o_lon + d_lon) / 2

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=12,
        tiles="CartoDB positron",
    )

    # Origin marker
    folium.Marker(
        location=[o_lat, o_lon],
        popup="Titik Asal",
        tooltip="Asal",
        icon=folium.Icon(color="green", icon="play", prefix="fa"),
    ).add_to(m)

    # Destination marker
    folium.Marker(
        location=[d_lat, d_lon],
        popup="Titik Tujuan",
        tooltip="Tujuan",
        icon=folium.Icon(color="red", icon="flag", prefix="fa"),
    ).add_to(m)

    # Route line
    route_color = "#2ecc71" if is_safe else "#e74c3c"
    folium.PolyLine(
        locations=[[o_lat, o_lon], [d_lat, d_lon]],
        color=route_color,
        weight=4,
        opacity=0.8,
        tooltip="Rute yang disarankan",
    ).add_to(m)

    st_folium(m, height=height, use_container_width=True, key=key)


# ---------------------------------------------------------------------------
# Route finder form
# ---------------------------------------------------------------------------


def render_route_finder(api_client: Any) -> None:
    """
    Render a form to find a safe route between two coordinates.

    Args:
        api_client: APIClient instance (or None for demo mode).
    """
    st.markdown("#### 🗺️ Cari Rute Aman")
    st.caption(
        "Masukkan koordinat asal dan tujuan untuk mendapatkan rute yang "
        "menghindari wilayah berisiko tinggi."
    )

    with st.form("route_finder_form"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Titik Asal**")
            o_lat = st.number_input(
                "Latitude Asal", value=-6.1174, format="%.4f", key="o_lat"
            )
            o_lon = st.number_input(
                "Longitude Asal", value=106.7942, format="%.4f", key="o_lon"
            )
        with col2:
            st.markdown("**Titik Tujuan**")
            d_lat = st.number_input(
                "Latitude Tujuan", value=-6.2441, format="%.4f", key="d_lat"
            )
            d_lon = st.number_input(
                "Longitude Tujuan", value=106.7971, format="%.4f", key="d_lon"
            )

        submitted = st.form_submit_button("Cari Rute Aman", use_container_width=True)

    if submitted:
        with st.spinner("Mencari rute aman..."):
            result = None
            if api_client is not None:
                result = api_client.find_safe_route(o_lat, o_lon, d_lat, d_lon)

            if result is None:
                # Demo fallback
                result = {
                    "origin": {"latitude": o_lat, "longitude": o_lon},
                    "destination": {"latitude": d_lat, "longitude": d_lon},
                    "is_safe": True,
                    "route_region_ids": [3, 4],
                    "avoided_regions": [1, 2],
                    "no_safe_route_reason": None,
                    "estimated_recovery_hours": None,
                }

        if result.get("is_safe"):
            avoided = result.get("avoided_regions", [])
            st.success(
                f"✅ Rute aman ditemukan! "
                f"Menghindari {len(avoided)} wilayah berisiko tinggi."
            )
        else:
            reason = result.get("no_safe_route_reason", "Semua jalur terdampak.")
            recovery = result.get("estimated_recovery_hours")
            msg = f"⚠️ Tidak ada rute aman tersedia. {reason}"
            if recovery:
                msg += f" Estimasi pemulihan: {recovery:.1f} jam."
            st.warning(msg)

        render_safe_route_map(result, key="route_result_map")


# ---------------------------------------------------------------------------
# Alternative facilities list
# ---------------------------------------------------------------------------


def render_alternative_facilities(facilities: List[Dict[str, Any]]) -> None:
    """
    Render a list of alternative facilities.

    Args:
        facilities: List of facility dicts with name, type, distance_km, etc.
    """
    if not facilities:
        st.info("Tidak ada fasilitas alternatif yang tersedia dalam radius 10 km.")
        return

    st.markdown("#### 🏥 Fasilitas Alternatif")
    for fac in facilities:
        name = fac.get("name", "Fasilitas")
        fac_type = fac.get("type", "")
        distance = fac.get("distance_km")
        is_operational = fac.get("is_operational", True)
        capacity = fac.get("capacity")

        status_icon = "✅" if is_operational else "❌"
        dist_text = f"{distance:.1f} km" if distance is not None else "—"
        cap_text = f"Kapasitas: {capacity}" if capacity else ""

        st.markdown(
            f"""
            <div style="
                background:#f8f9fa;
                border:1px solid #dee2e6;
                border-radius:6px;
                padding:10px 14px;
                margin-bottom:8px;
            ">
                <div style="font-weight:bold;color:#2c3e50;">{status_icon} {name}</div>
                <div style="font-size:13px;color:#555;margin-top:4px;">
                    {fac_type} &nbsp;|&nbsp; {dist_text}
                    {"&nbsp;|&nbsp;" + cap_text if cap_text else ""}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Main render function
# ---------------------------------------------------------------------------


def render_recommendation_panel(
    recommendations: List[Dict[str, Any]],
    api_client: Any = None,
    show_route_finder: bool = True,
    alternative_facilities: Optional[List[Dict[str, Any]]] = None,
) -> None:
    """
    Render the full recommendation panel.

    Displays:
    - Recommendations grouped by urgency level
    - Route finder form (optional)
    - Alternative facilities list (optional)

    Args:
        recommendations: List of recommendation dicts.
        api_client: APIClient instance for route finding.
        show_route_finder: Whether to show the route finder form.
        alternative_facilities: Optional list of alternative facility dicts.
    """
    if not recommendations:
        st.info(
            "Tidak ada rekomendasi aktif untuk wilayah ini saat ini. "
            "Kondisi dalam batas normal."
        )
    else:
        # Group by urgency
        grouped: Dict[str, List[Dict[str, Any]]] = {
            "Segera": [],
            "Waspada": [],
            "Siaga": [],
        }
        for rec in recommendations:
            urgency = rec.get("urgency", "Siaga")
            grouped.setdefault(urgency, []).append(rec)

        for urgency in ["Segera", "Waspada", "Siaga"]:
            recs = grouped.get(urgency, [])
            if not recs:
                continue
            cfg = URGENCY_CONFIG.get(urgency, URGENCY_CONFIG["Siaga"])
            st.markdown(
                f"#### {cfg['icon']} {urgency} "
                f"<span style='font-size:13px;color:#888;font-weight:normal;'>"
                f"({cfg['description']})</span>",
                unsafe_allow_html=True,
            )
            for rec in recs:
                _render_recommendation_card(rec)

    # Alternative facilities
    if alternative_facilities is not None:
        st.markdown("---")
        render_alternative_facilities(alternative_facilities)

    # Route finder
    if show_route_finder:
        st.markdown("---")
        render_route_finder(api_client)
