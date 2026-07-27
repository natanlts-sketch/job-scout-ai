from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is importable when Streamlit starts from app/
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

from i18n import apply_direction, sync_lang_from_prefs, t
from src.auth import get_preferences, get_user_by_id
from src.core.db import initialize_database


def require_user() -> dict:
    initialize_database()
    user_id = st.session_state.get("user_id")
    if user_id:
        sync_lang_from_prefs(get_preferences(user_id))
    apply_direction()
    if not user_id:
        st.warning(t("please_login"))
        st.page_link("Home.py", label=t("go_home"))
        st.stop()
    user = get_user_by_id(user_id)
    if not user:
        st.session_state.clear()
        st.warning(t("session_expired"))
        st.page_link("Home.py", label=t("go_home"))
        st.stop()
    return user
