"""
Filter and parameter selection component for URIS-AI dashboard.

Provides sidebar widgets for:
- Time range selection
- Risk category filter
- Region selection

Requirements: 6.2
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Filter state keys
# ---------------------------------------------------------------------------

FILTER_STATE_KEYS = {
    "time_range_hours": "filter_time_range_hours",
    "risk_categories": "filter_risk_categories",
    "selected_region_id": "selected_region_id",
}

RISK_CATEGORIES = ["RENDAH", "SEDANG", "TINGGI", "KRITIS"]

RISK_CATEGORY_LABELS = {
    "RENDAH": "🟢 Rendah",
    "SEDANG": "🟡 Sedang",
    "TINGGI": "🔴 Tinggi",
    "KRITIS": "🟣 Kritis",
}

TIME_RANGE_OPTIONS: Dict[str, int] = {
    "1 jam terakhir": 1,
    "6 jam terakhir": 6,
    "12 jam terakhir": 12,
    "24 jam terakhir": 24,
    "48 jam terakhir": 48,
    "7 hari terakhir": 168,
}


# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------


def _init_filter_state() -> None:
    """Ensure filter-related session state keys exist with defaults."""
    defaults: Dict[str, Any] = {
        FILTER_STATE_KEYS["time_range_hours"]: 24,
        FILTER_STATE_KEYS["risk_categories"]: list(RISK_CATEGORIES),
        FILTER_STATE_KEYS["selected_region_id"]: None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_filter_values() -> Dict[str, Any]:
    """
    Return the current filter values from session state.

    Returns:
        Dict with keys: time_range_hours, risk_categories, selected_region_id
    """
    _init_filter_state()
    return {
        "time_range_hours": st.session_state.get(
            FILTER_STATE_KEYS["time_range_hours"], 24
        ),
        "risk_categories": st.session_state.get(
            FILTER_STATE_KEYS["risk_categories"], list(RISK_CATEGORIES)
        ),
        "selected_region_id": st.session_state.get(
            FILTER_STATE_KEYS["selected_region_id"]
        ),
    }


def apply_risk_category_filter(
    regions: List[Dict[str, Any]],
    selected_categories: List[str],
) -> List[Dict[str, Any]]:
    """
    Filter a list of region dicts by risk category.

    Args:
        regions: Full list of region dicts.
        selected_categories: List of category strings to include.

    Returns:
        Filtered list of region dicts.
    """
    if not selected_categories or set(selected_categories) == set(RISK_CATEGORIES):
        return regions
    return [
        r for r in regions
        if r.get("risk_category", "RENDAH") in selected_categories
    ]


# ---------------------------------------------------------------------------
# Sidebar filter widgets
# ---------------------------------------------------------------------------


def render_filters(
    regions: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Render filter widgets in the Streamlit sidebar.

    Displays:
    - Time range selector
    - Risk category multi-select
    - Region selector (if regions list provided)

    Args:
        regions: Optional list of region dicts for the region selector.

    Returns:
        Dict with current filter values:
        {time_range_hours, risk_categories, selected_region_id}
    """
    _init_filter_state()

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔍 Filter & Parameter")

    # ------------------------------------------------------------------
    # Time range filter
    # ------------------------------------------------------------------
    time_options = list(TIME_RANGE_OPTIONS.keys())
    current_hours = st.session_state.get(FILTER_STATE_KEYS["time_range_hours"], 24)
    current_label = next(
        (label for label, h in TIME_RANGE_OPTIONS.items() if h == current_hours),
        "24 jam terakhir",
    )
    current_idx = time_options.index(current_label) if current_label in time_options else 3

    selected_time_label = st.sidebar.selectbox(
        "⏱️ Rentang Waktu",
        options=time_options,
        index=current_idx,
        key="sidebar_time_range",
        help="Pilih rentang waktu untuk data yang ditampilkan",
    )
    selected_hours = TIME_RANGE_OPTIONS[selected_time_label]
    st.session_state[FILTER_STATE_KEYS["time_range_hours"]] = selected_hours

    # ------------------------------------------------------------------
    # Risk category filter
    # ------------------------------------------------------------------
    current_cats = st.session_state.get(
        FILTER_STATE_KEYS["risk_categories"], list(RISK_CATEGORIES)
    )
    category_labels = [RISK_CATEGORY_LABELS[c] for c in RISK_CATEGORIES]
    current_labels = [RISK_CATEGORY_LABELS[c] for c in current_cats if c in RISK_CATEGORY_LABELS]

    selected_labels = st.sidebar.multiselect(
        "🎯 Kategori Risiko",
        options=category_labels,
        default=current_labels,
        key="sidebar_risk_categories",
        help="Pilih kategori risiko yang ingin ditampilkan pada peta",
    )

    # Map labels back to category keys
    label_to_key = {v: k for k, v in RISK_CATEGORY_LABELS.items()}
    selected_categories = [label_to_key[lbl] for lbl in selected_labels if lbl in label_to_key]
    if not selected_categories:
        selected_categories = list(RISK_CATEGORIES)  # default to all if none selected
    st.session_state[FILTER_STATE_KEYS["risk_categories"]] = selected_categories

    # ------------------------------------------------------------------
    # Region selector
    # ------------------------------------------------------------------
    selected_region_id: Optional[int] = st.session_state.get(
        FILTER_STATE_KEYS["selected_region_id"]
    )

    if regions:
        region_options: Dict[str, Optional[int]] = {"— Semua wilayah —": None}
        for r in regions:
            name = r.get("region_name", f"Wilayah {r.get('region_id')}")
            region_options[name] = r.get("region_id")

        region_names = list(region_options.keys())
        current_region_name = next(
            (name for name, rid in region_options.items() if rid == selected_region_id),
            "— Semua wilayah —",
        )
        current_region_idx = (
            region_names.index(current_region_name)
            if current_region_name in region_names
            else 0
        )

        chosen_region = st.sidebar.selectbox(
            "📍 Wilayah",
            options=region_names,
            index=current_region_idx,
            key="sidebar_region_selector",
            help="Pilih wilayah untuk melihat detail risiko",
        )
        new_region_id = region_options.get(chosen_region)
        if new_region_id != selected_region_id:
            st.session_state[FILTER_STATE_KEYS["selected_region_id"]] = new_region_id
            selected_region_id = new_region_id

    # ------------------------------------------------------------------
    # Reset button
    # ------------------------------------------------------------------
    if st.sidebar.button("🔄 Reset Filter", key="reset_filters", use_container_width=True):
        st.session_state[FILTER_STATE_KEYS["time_range_hours"]] = 24
        st.session_state[FILTER_STATE_KEYS["risk_categories"]] = list(RISK_CATEGORIES)
        st.session_state[FILTER_STATE_KEYS["selected_region_id"]] = None
        st.rerun()

    return {
        "time_range_hours": selected_hours,
        "risk_categories": selected_categories,
        "selected_region_id": selected_region_id,
    }


# ---------------------------------------------------------------------------
# Inline filter summary
# ---------------------------------------------------------------------------


def render_filter_summary(filters: Dict[str, Any]) -> None:
    """
    Render a compact summary of active filters below the page header.

    Args:
        filters: Dict returned by render_filters().
    """
    hours = filters.get("time_range_hours", 24)
    cats = filters.get("risk_categories", RISK_CATEGORIES)
    region_id = filters.get("selected_region_id")

    time_label = next(
        (label for label, h in TIME_RANGE_OPTIONS.items() if h == hours),
        f"{hours} jam",
    )

    cat_labels = [RISK_CATEGORY_LABELS.get(c, c) for c in cats]
    cats_text = ", ".join(cat_labels) if len(cats) < 4 else "Semua kategori"

    region_text = f"Wilayah #{region_id}" if region_id else "Semua wilayah"

    st.caption(
        f"📊 Menampilkan: **{time_label}** | "
        f"Kategori: **{cats_text}** | "
        f"Wilayah: **{region_text}**"
    )
