from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is importable when Streamlit starts from app/
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

from brand import apply_brand_theme, render_sidebar_brand
from i18n import sync_lang_from_prefs, t
from session_cookie import clear_session_cookie, read_session_cookie
from src.auth import get_preferences, get_user_by_id, get_user_by_session_token, revoke_session_token
from src.core.db import initialize_database


def require_user() -> dict:
    initialize_database()
    apply_brand_theme()
    render_sidebar_brand()

    user_id = st.session_state.get("user_id")
    user = get_user_by_id(user_id) if user_id else None

    if not user:
        token = read_session_cookie()
        user = get_user_by_session_token(token)
        if user:
            st.session_state["user_id"] = user["id"]
            st.session_state["session_token"] = token
            sync_lang_from_prefs(get_preferences(user["id"]))

    if not user:
        st.warning(t("please_login"))
        st.page_link("Home.py", label=t("go_home"))
        st.stop()

    sync_lang_from_prefs(get_preferences(user["id"]))
    st.sidebar.write(f"{t('signed_in_as')} **{user.get('display_name') or user['email']}**")
    if st.sidebar.button(t("log_out"), key="sidebar_logout"):
        token = st.session_state.get("session_token") or read_session_cookie()
        revoke_session_token(token)
        clear_session_cookie()
        st.session_state.clear()
        st.rerun()
    return user
