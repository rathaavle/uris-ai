"""
Map Visualizer component for URIS-AI dashboard.

Renders an interactive choropleth map of Urban Risk Scores using Folium.
Supports zoom, pan, and click interactions.

Requirements: 6.2, 4.2
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional

import folium
import streamlit as st

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Risk category colour palette
# ---------------------------------------------------------------------------

RISK_COLORS: Dict[str, str] = {
    "RENDAH": "#2ecc71",   # green
    "SEDANG": "#f39c12",   # orange
    "TINGGI": "#e74c3c",   # red
    "KRITIS": "#8e44ad",   # purple
}

RISK_FILL_OPACITY = 0.65
CIRCLE_RADIUS_PX = 14  # pixels – radius for CircleMarker (screen-space, not metres)


def _urs_to_color(urs: float) -> str:
    """Map a numeric Urban Risk Score (0-100) to a hex colour."""
    if urs < 26:
        return RISK_COLORS["RENDAH"]
    elif urs < 51:
        return RISK_COLORS["SEDANG"]
    elif urs < 76:
        return RISK_COLORS["TINGGI"]
    else:
        return RISK_COLORS["KRITIS"]


def _urs_to_category(urs: float) -> str:
    """Map a numeric URS to a category label."""
    if urs < 26:
        return "RENDAH"
    elif urs < 51:
        return "SEDANG"
    elif urs < 76:
        return "TINGGI"
    else:
        return "KRITIS"


# ---------------------------------------------------------------------------
# Map builder
# ---------------------------------------------------------------------------


def build_risk_map(
    regions: List[Dict[str, Any]],
    selected_region_id: Optional[int] = None,
    on_region_click: Optional[Callable[[int], None]] = None,
    center_lat: float = -6.2088,
    center_lon: float = 106.8456,
    zoom_start: int = 11,
) -> folium.Map:
    """
    Build a Folium map with choropleth-style circle markers for each region.

    Each marker is coloured by risk category and shows a popup with key metrics.
    Clicking a marker stores the region_id in Streamlit session state.

    Args:
        regions: List of region dicts (from API or demo data).
        selected_region_id: Currently selected region (highlighted with border).
        on_region_click: Optional callback – not used directly (Folium handles
            clicks via JS; selection is managed via session_state).
        center_lat: Initial map centre latitude.
        center_lon: Initial map centre longitude.
        zoom_start: Initial zoom level.

    Returns:
        Configured folium.Map instance.
    """
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom_start,
        tiles="CartoDB positron",
        control_scale=True,
    )

    # Add a legend
    legend_html = _build_legend_html()
    m.get_root().html.add_child(folium.Element(legend_html))

    for region in regions:
        lat = region.get("latitude")
        lon = region.get("longitude")
        if lat is None or lon is None:
            continue

        urs = float(region.get("urban_risk_score", 0))
        category = region.get("risk_category") or _urs_to_category(urs)
        color = RISK_COLORS.get(category, _urs_to_color(urs))
        region_id = region.get("region_id")
        name = region.get("region_name", f"Wilayah {region_id}")

        is_selected = region_id == selected_region_id
        border_color = "#2c3e50" if is_selected else color
        border_weight = 4 if is_selected else 1.5

        popup_html = _build_popup_html(region)
        tooltip_text = (
            f"<b>{name}</b><br>"
            f"URS: {urs:.1f} | {category}"
        )

        folium.CircleMarker(
            location=[lat, lon],
            radius=CIRCLE_RADIUS_PX,
            color=border_color,
            weight=border_weight,
            fill=True,
            fill_color=color,
            fill_opacity=RISK_FILL_OPACITY,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=folium.Tooltip(tooltip_text),
        ).add_to(m)

    # Layer control
    folium.LayerControl().add_to(m)

    return m


def _build_popup_html(region: Dict[str, Any]) -> str:
    """Build an HTML popup string for a region marker."""
    name = region.get("region_name", f"Wilayah {region.get('region_id')}")
    urs = float(region.get("urban_risk_score", 0))
    category = region.get("risk_category") or _urs_to_category(urs)
    flood_risk = float(region.get("flood_risk", 0))
    traffic = float(region.get("traffic_impact", 0))
    service = float(region.get("service_access", 0))
    color = RISK_COLORS.get(category, "#999")

    return f"""
    <div style="font-family: Arial, sans-serif; min-width: 220px;">
        <h4 style="margin:0 0 8px 0; color:#2c3e50;">{name}</h4>
        <div style="background:{color}; color:white; padding:4px 8px;
                    border-radius:4px; display:inline-block; margin-bottom:8px;
                    font-weight:bold;">
            {category}
        </div>
        <table style="width:100%; border-collapse:collapse; font-size:13px;">
            <tr>
                <td style="padding:3px 0; color:#555;">Urban Risk Score</td>
                <td style="padding:3px 0; font-weight:bold; text-align:right;">
                    {urs:.1f} / 100
                </td>
            </tr>
            <tr>
                <td style="padding:3px 0; color:#555;">Risiko Banjir</td>
                <td style="padding:3px 0; text-align:right;">{flood_risk:.1f}</td>
            </tr>
            <tr>
                <td style="padding:3px 0; color:#555;">Dampak Lalu Lintas</td>
                <td style="padding:3px 0; text-align:right;">{traffic:.1f}</td>
            </tr>
            <tr>
                <td style="padding:3px 0; color:#555;">Aksesibilitas Layanan</td>
                <td style="padding:3px 0; text-align:right;">{service:.1f}</td>
            </tr>
        </table>
        <p style="margin:8px 0 0 0; font-size:11px; color:#888;">
            Klik untuk melihat detail wilayah
        </p>
    </div>
    """


def _build_legend_html() -> str:
    """Build an HTML legend element for the map."""
    items = "".join(
        f'<div style="display:flex;align-items:center;margin-bottom:4px;">'
        f'<div style="width:16px;height:16px;background:{color};border-radius:50%;'
        f'margin-right:8px;border:1px solid #ccc;"></div>'
        f'<span style="font-size:12px;">{label}</span></div>'
        for label, color in [
            ("Rendah (0–25)", RISK_COLORS["RENDAH"]),
            ("Sedang (26–50)", RISK_COLORS["SEDANG"]),
            ("Tinggi (51–75)", RISK_COLORS["TINGGI"]),
            ("Kritis (76–100)", RISK_COLORS["KRITIS"]),
        ]
    )
    return f"""
    <div style="
        position: fixed;
        bottom: 30px; right: 10px;
        z-index: 1000;
        background: white;
        padding: 10px 14px;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        font-family: Arial, sans-serif;
    ">
        <b style="font-size:13px;">Tingkat Risiko</b>
        <div style="margin-top:6px;">{items}</div>
    </div>
    """


# ---------------------------------------------------------------------------
# Streamlit render function
# ---------------------------------------------------------------------------


def render_map(
    regions: List[Dict[str, Any]],
    height: int = 500,
    key: str = "risk_map",
) -> Optional[int]:
    """
    Render the interactive risk map inside a Streamlit container.

    Displays a Folium choropleth map and a region selector below it.
    Returns the selected region_id (int) or None.

    Args:
        regions: List of region dicts with lat/lon and risk data.
        height: Map height in pixels.
        key: Unique Streamlit widget key.

    Returns:
        Selected region_id or None.
    """
    try:
        from streamlit_folium import st_folium  # type: ignore[import]
    except ImportError:
        st.error(
            "Paket `streamlit-folium` belum terpasang. "
            "Jalankan: `pip install streamlit-folium`"
        )
        return None

    if not regions:
        st.info("Tidak ada data wilayah yang tersedia saat ini.")
        return None

    selected_id: Optional[int] = st.session_state.get("selected_region_id")

    # Build and render the map
    fmap = build_risk_map(regions, selected_region_id=selected_id)
    map_data = st_folium(fmap, height=height, use_container_width=True, key=key)

    # Handle click events from the map
    if map_data and map_data.get("last_object_clicked_popup"):
        # Parse region_id from popup click – we use the region selector below
        pass

    # Region selector (accessible alternative to map click)
    region_options = {
        r.get("region_name", f"Wilayah {r.get('region_id')}"): r.get("region_id")
        for r in regions
    }
    region_names = ["— Pilih wilayah —"] + list(region_options.keys())

    current_name = next(
        (
            name
            for name, rid in region_options.items()
            if rid == selected_id
        ),
        "— Pilih wilayah —",
    )

    chosen = st.selectbox(
        "Pilih wilayah untuk melihat detail:",
        options=region_names,
        index=region_names.index(current_name) if current_name in region_names else 0,
        key=f"{key}_selector",
    )

    if chosen != "— Pilih wilayah —":
        new_id = region_options.get(chosen)
        if new_id != selected_id:
            st.session_state["selected_region_id"] = new_id
            st.rerun()
        return new_id

    return None


# ---------------------------------------------------------------------------
# Summary statistics bar
# ---------------------------------------------------------------------------


def render_map_summary(regions: List[Dict[str, Any]]) -> None:
    """Render a row of metric cards summarising risk across all regions."""
    if not regions:
        return

    total = len(regions)
    counts: Dict[str, int] = {"RENDAH": 0, "SEDANG": 0, "TINGGI": 0, "KRITIS": 0}
    for r in regions:
        cat = r.get("risk_category") or _urs_to_category(float(r.get("urban_risk_score", 0)))
        counts[cat] = counts.get(cat, 0) + 1

    cols = st.columns(5)
    cols[0].metric("Total Wilayah", total)
    cols[1].metric("🟢 Rendah", counts["RENDAH"])
    cols[2].metric("🟡 Sedang", counts["SEDANG"])
    cols[3].metric("🔴 Tinggi", counts["TINGGI"])
    cols[4].metric("🟣 Kritis", counts["KRITIS"])
