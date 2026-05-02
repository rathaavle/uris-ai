"""
User Interface component for URIS-AI dashboard.

Handles login form, Azure AD integration (optional), and role-based UI rendering.

Requirements: 10.1, 10.3
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import streamlit as st

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Role definitions
# ---------------------------------------------------------------------------

ROLES = {
    "public": {
        "label": "Masyarakat Umum",
        "allowed_pages": ["Peta Risiko", "Navigasi Rute"],
        "description": "Akses ke peta risiko publik dan navigasi rute alternatif.",
    },
    "facility_manager": {
        "label": "Pengelola Fasilitas",
        "allowed_pages": ["Peta Risiko", "Detail Wilayah", "Rekomendasi", "Navigasi Rute"],
        "description": "Akses ke informasi fasilitas dan rekomendasi operasional.",
    },
    "government": {
        "label": "Pemerintah",
        "allowed_pages": [
            "Peta Risiko",
            "Detail Wilayah",
            "Rekomendasi",
            "Analitik",
            "Navigasi Rute",
        ],
        "description": "Akses penuh ke semua fitur sistem.",
    },
}

# ---------------------------------------------------------------------------
# Session state helpers
# ---------------------------------------------------------------------------


def _init_auth_state() -> None:
    """Ensure auth-related session state keys exist."""
    defaults: Dict[str, Any] = {
        "authenticated": False,
        "user": None,
        "token": None,
        "role": None,
        "login_error": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def is_authenticated() -> bool:
    """Return True if the current session has a valid authenticated user."""
    _init_auth_state()
    return bool(st.session_state.get("authenticated", False))


def get_current_role() -> Optional[str]:
    """Return the role string of the authenticated user, or None."""
    return st.session_state.get("role")


def get_current_user() -> Optional[Dict[str, Any]]:
    """Return the authenticated user dict, or None."""
    return st.session_state.get("user")


def can_access_page(page: str) -> bool:
    """
    Return True if the current user's role allows access to *page*.

    Masyarakat Umum can only access map visualization, public risk info,
    and route navigation (Req 10.3).
    """
    role = get_current_role()
    if role is None:
        # Unauthenticated users can only see the public map
        return page in ("Peta Risiko",)
    role_info = ROLES.get(role, {})
    return page in role_info.get("allowed_pages", [])


def logout() -> None:
    """Clear authentication state."""
    st.session_state["authenticated"] = False
    st.session_state["user"] = None
    st.session_state["token"] = None
    st.session_state["role"] = None
    st.session_state["login_error"] = None


# ---------------------------------------------------------------------------
# MSAL / Azure AD integration (optional)
# ---------------------------------------------------------------------------


def _try_azure_ad_login(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Attempt login via MSAL (Azure AD).

    Returns a token dict on success, None if MSAL is not configured or fails.
    This is intentionally optional so the app works in dev mode without Azure AD.
    """
    try:
        import msal  # type: ignore[import]
        import os

        tenant_id = os.environ.get("AZURE_AD_TENANT_ID", "")
        client_id = os.environ.get("AZURE_AD_CLIENT_ID", "")
        client_secret = os.environ.get("AZURE_AD_CLIENT_SECRET", "")

        if not all([tenant_id, client_id, client_secret]):
            logger.debug("Azure AD credentials not configured – skipping MSAL login.")
            return None

        authority = f"https://login.microsoftonline.com/{tenant_id}"
        app = msal.ConfidentialClientApplication(
            client_id=client_id,
            authority=authority,
            client_credential=client_secret,
        )
        scopes = [f"api://{client_id}/.default"]
        result = app.acquire_token_by_username_password(
            username=username, password=password, scopes=scopes
        )
        if "access_token" in result:
            return result
        logger.warning("MSAL login failed: %s", result.get("error_description"))
        return None
    except ImportError:
        logger.debug("msal package not installed – Azure AD login unavailable.")
        return None
    except Exception as exc:
        logger.warning("MSAL login error: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Login form
# ---------------------------------------------------------------------------


def render_login_form(api_client: Any) -> bool:
    """
    Render the login form and handle authentication.

    Tries Azure AD first (if configured), then falls back to the FastAPI
    backend's /auth/login endpoint.  In demo mode (no backend), accepts
    hard-coded demo credentials.

    Returns True if the user just logged in successfully.
    """
    _init_auth_state()

    st.markdown("## 🔐 Masuk ke URIS-AI")
    st.markdown(
        "Silakan masuk untuk mengakses fitur lengkap sistem. "
        "Masyarakat umum dapat menggunakan peta risiko tanpa login."
    )

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username / Email", placeholder="contoh: user@example.com")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Masuk", use_container_width=True)

    if submitted:
        if not username or not password:
            st.error("Username dan password tidak boleh kosong.")
            return False

        # 1. Try Azure AD
        msal_result = _try_azure_ad_login(username, password)
        if msal_result:
            st.session_state["authenticated"] = True
            st.session_state["token"] = msal_result.get("access_token")
            st.session_state["role"] = "government"  # default for AD users
            st.session_state["user"] = {"username": username, "role": "government"}
            st.session_state["login_error"] = None
            st.success("Login berhasil via Azure AD!")
            return True

        # 2. Try FastAPI backend
        if api_client is not None:
            result = api_client.login(username, password)
            if result and "access_token" in result:
                api_client.set_token(result["access_token"])
                user_info = api_client.get_current_user() or {}
                role = result.get("role", user_info.get("role", "public"))
                st.session_state["authenticated"] = True
                st.session_state["token"] = result["access_token"]
                st.session_state["role"] = role
                st.session_state["user"] = user_info or {"username": username, "role": role}
                st.session_state["login_error"] = None
                st.success("Login berhasil!")
                return True

        # 3. Demo mode fallback
        demo_users = {
            "admin": ("admin123", "government"),
            "pengelola": ("pengelola123", "facility_manager"),
            "publik": ("publik123", "public"),
        }
        if username in demo_users:
            demo_pass, demo_role = demo_users[username]
            if password == demo_pass:
                st.session_state["authenticated"] = True
                st.session_state["token"] = "demo-token"
                st.session_state["role"] = demo_role
                st.session_state["user"] = {
                    "username": username,
                    "role": demo_role,
                    "email": f"{username}@demo.uris-ai.id",
                }
                st.session_state["login_error"] = None
                st.success("Login berhasil (mode demo)!")
                return True

        st.error("Username atau password salah. Silakan coba lagi.")
        return False

    return False


# ---------------------------------------------------------------------------
# User info sidebar widget
# ---------------------------------------------------------------------------


def render_user_info() -> None:
    """
    Render the authenticated user's info and a logout button in the sidebar.
    """
    _init_auth_state()
    user = get_current_user()
    role = get_current_role()

    if user and role:
        role_label = ROLES.get(role, {}).get("label", role)
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"👤 **{user.get('username', 'Pengguna')}**")
        st.sidebar.markdown(f"🏷️ {role_label}")
        if st.sidebar.button("Keluar", key="logout_btn", use_container_width=True):
            logout()
            st.rerun()
    else:
        st.sidebar.markdown("---")
        st.sidebar.markdown("👤 *Belum masuk*")


# ---------------------------------------------------------------------------
# Access denied message
# ---------------------------------------------------------------------------


def render_access_denied(page: str) -> None:
    """Show a friendly access-denied message for the given page."""
    st.warning(
        f"⛔ Akses ke halaman **{page}** tidak diizinkan untuk peran Anda. "
        "Silakan masuk dengan akun yang memiliki izin yang sesuai."
    )
