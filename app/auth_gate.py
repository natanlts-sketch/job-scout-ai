from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

from brand import apply_brand_theme, render_top_bar
from i18n import sync_lang_from_prefs, t
from session_cookie import clear_session_token, read_session_token, write_session_token
from src.auth import get_preferences, get_user_by_id, get_user_by_session_token, revoke_session_token
from src.core.db import initialize_database


def require_user() -> dict:
    initialize_database()
    apply_brand_theme()

    user_id = st.session_state.get("user_id")
    user = get_user_by_id(user_id) if user_id else None

    if not user:
        token = read_session_token()
        user = get_user_by_session_token(token)
        if user:
            st.session_state["user_id"] = user["id"]
            write_session_token(token or "")
            sync_lang_from_prefs(get_preferences(user["id"]))

    if not user:
        st.warning(t("please_login"))
        st.page_link("Home.py", label=t("go_home"))
        st.stop()

    sync_lang_from_prefs(get_preferences(user["id"]))
    label = user.get("display_name") or user["email"]
    if render_top_bar(user_label=label, logout_key="top_logout"):
        token = read_session_token()
        revoke_session_token(token)
        clear_session_token()
        st.session_state.clear()
        st.rerun()
    return user
