"""
Risk Dashboard component for URIS-AI.

Displays Urban Risk Score, risk category, confidence, and risk trend chart
for a selected region.

Requirements: 6.6, 4.2
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import plotly.graph_objects as go
import streamlit as st

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Colour helpers (consistent with map_visualizer)
# ---------------------------------------------------------------------------

RISK_COLORS: Dict[str, str] = {
    "RENDAH": "#2ecc71",
    "SEDANG": "#f39c12",
    "TINGGI": "#e74c3c",
    "KRITIS": "#8e44ad",
}

RISK_LABELS: Dict[str, str] = {
    "RENDAH": "Rendah",
    "SEDANG": "Sedang",
    "TINGGI": "Tinggi",
    "KRITIS": "Kritis",
}

RISK_DESCRIPTIONS: Dict[str, str] = {
    "RENDAH": "Kondisi normal. Tidak ada tindakan khusus yang diperlukan.",
    "SEDANG": "Waspadai perkembangan cuaca. Pantau informasi terbaru.",
    "TINGGI": "Risiko signifikan. Persiapkan langkah mitigasi dan evakuasi.",
    "KRITIS": "Bahaya tinggi! Segera lakukan evakuasi dan aktifkan protokol darurat.",
}


def _urs_to_category(urs: float) -> str:
    if urs < 26:
        return "RENDAH"
    elif urs < 51:
        return "SEDANG"
    elif urs < 76:
        return "TINGGI"
    else:
        return "KRITIS"


# ---------------------------------------------------------------------------
# URS gauge chart
# ---------------------------------------------------------------------------


def _build_urs_gauge(urs: float, category: str) -> go.Figure:
    """Build a Plotly gauge chart for the Urban Risk Score."""
    color = RISK_COLORS.get(category, "#999")

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=urs,
            number={"suffix": " / 100", "font": {"size": 22}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#555"},
                "bar": {"color": color, "thickness": 0.3},
                "bgcolor": "white",
                "borderwidth": 2,
                "bordercolor": "#ccc",
                "steps": [
                    {"range": [0, 25], "color": "#d5f5e3"},
                    {"range": [25, 50], "color": "#fdebd0"},
                    {"range": [50, 75], "color": "#fadbd8"},
                    {"range": [75, 100], "color": "#e8daef"},
                ],
                "threshold": {
                    "line": {"color": color, "width": 4},
                    "thickness": 0.75,
                    "value": urs,
                },
            },
            title={"text": "Urban Risk Score", "font": {"size": 16}},
        )
    )
    fig.update_layout(
        height=220,
        margin={"t": 40, "b": 10, "l": 20, "r": 20},
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


# ---------------------------------------------------------------------------
# Risk trend chart
# ---------------------------------------------------------------------------


def _build_trend_chart(trend_data: List[Dict[str, Any]], region_name: str) -> go.Figure:
    """Build a Plotly line chart for the risk trend."""
    if not trend_data:
        fig = go.Figure()
        fig.update_layout(
            title="Tren Risiko (tidak ada data)",
            height=220,
            paper_bgcolor="rgba(0,0,0,0)",
        )
        return fig

    dates = [point.get("date", "") for point in trend_data]
    scores = [float(point.get("urban_risk_score", 0)) for point in trend_data]

    # Colour each segment by risk level
    colors = [RISK_COLORS.get(_urs_to_category(s), "#999") for s in scores]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=scores,
            mode="lines+markers",
            name="URS",
            line={"color": "#3498db", "width": 2},
            marker={"color": colors, "size": 7, "line": {"width": 1, "color": "white"}},
            hovertemplate="<b>%{x}</b><br>URS: %{y:.1f}<extra></extra>",
        )
    )

    # Threshold lines
    for threshold, label, color in [
        (25, "Rendah/Sedang", RISK_COLORS["SEDANG"]),
        (50, "Sedang/Tinggi", RISK_COLORS["TINGGI"]),
        (75, "Tinggi/Kritis", RISK_COLORS["KRITIS"]),
    ]:
        fig.add_hline(
            y=threshold,
            line_dash="dot",
            line_color=color,
            opacity=0.5,
            annotation_text=label,
            annotation_position="right",
            annotation_font_size=10,
        )

    fig.update_layout(
        title=f"Tren Risiko – {region_name}",
        xaxis_title="Waktu",
        yaxis_title="Urban Risk Score",
        yaxis={"range": [0, 100]},
        height=260,
        margin={"t": 50, "b": 40, "l": 50, "r": 80},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    return fig


# ---------------------------------------------------------------------------
# Component score breakdown
# ---------------------------------------------------------------------------


def _render_score_breakdown(region: Dict[str, Any]) -> None:
    """Render a three-column breakdown of component scores."""
    flood = float(region.get("flood_risk", 0))
    traffic = float(region.get("traffic_impact", 0))
    service = float(region.get("service_access", 0))

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            label="🌊 Risiko Banjir",
            value=f"{flood:.1f}",
            help="Skor risiko banjir berdasarkan data cuaca dan historis (0–100)",
        )
    with col2:
        st.metric(
            label="🚗 Dampak Lalu Lintas",
            value=f"{traffic:.1f}",
            help="Estimasi dampak banjir terhadap kondisi lalu lintas (0–100)",
        )
    with col3:
        st.metric(
            label="🏥 Aksesibilitas Layanan",
            value=f"{service:.1f}",
            help="Skor aksesibilitas fasilitas publik (0–100)",
        )


# ---------------------------------------------------------------------------
# Main render function
# ---------------------------------------------------------------------------


def render_risk_dashboard(
    region: Dict[str, Any],
    trend_data: Optional[List[Dict[str, Any]]] = None,
) -> None:
    """
    Render the full risk dashboard panel for a selected region.

    Displays:
    - Region name and last-updated timestamp
    - URS gauge chart
    - Risk category badge with description
    - Component score breakdown
    - Risk trend chart (if trend_data provided)

    Args:
        region: Region risk dict (from API or demo data).
        trend_data: Optional list of trend points [{date, urban_risk_score}].
    """
    if not region:
        st.info("Pilih wilayah pada peta untuk melihat detail risiko.")
        return

    region_name = region.get("region_name", f"Wilayah {region.get('region_id')}")
    urs = float(region.get("urban_risk_score", 0))
    category = region.get("risk_category") or _urs_to_category(urs)
    calculated_at = region.get("calculated_at", "")

    # Header
    st.markdown(f"### 📍 {region_name}")
    if calculated_at:
        # Show only date+time portion
        ts = str(calculated_at)[:19].replace("T", " ")
        st.caption(f"Diperbarui: {ts}")

    # Gauge + category side by side
    col_gauge, col_cat = st.columns([1, 1])
    with col_gauge:
        fig_gauge = _build_urs_gauge(urs, category)
        st.plotly_chart(fig_gauge, use_container_width=True, config={"displayModeBar": False})

    with col_cat:
        color = RISK_COLORS.get(category, "#999")
        label = RISK_LABELS.get(category, category)
        desc = RISK_DESCRIPTIONS.get(category, "")
        st.markdown(
            f"""
            <div style="
                background:{color};
                color:white;
                padding:12px 16px;
                border-radius:8px;
                margin-top:20px;
                text-align:center;
            ">
                <div style="font-size:28px; font-weight:bold;">{label}</div>
                <div style="font-size:13px; margin-top:4px; opacity:0.9;">
                    Kategori Risiko
                </div>
            </div>
            <p style="margin-top:12px; font-size:14px; color:#555;">{desc}</p>
            """,
            unsafe_allow_html=True,
        )

        # Display confidence if available from API
        confidence = region.get("confidence")
        if confidence is not None:
            try:
                conf_pct = float(confidence) * 100 if float(confidence) <= 1.0 else float(confidence)
                st.metric(
                    label="🎯 Tingkat Kepercayaan",
                    value=f"{conf_pct:.1f}%",
                    help="Tingkat kepercayaan model terhadap prediksi risiko ini (0–100%)",
                )
            except (TypeError, ValueError):
                logger.warning("Invalid confidence value: %s", confidence)

    st.markdown("---")

    # Component breakdown
    st.markdown("#### Komponen Risiko")
    _render_score_breakdown(region)

    # Trend chart
    if trend_data is not None:
        st.markdown("---")
        st.markdown("#### Tren Risiko (24 Jam Terakhir)")
        fig_trend = _build_trend_chart(trend_data, region_name)
        st.plotly_chart(fig_trend, use_container_width=True, config={"displayModeBar": False})
    else:
        st.markdown("---")
        st.caption("Data tren tidak tersedia saat ini.")
