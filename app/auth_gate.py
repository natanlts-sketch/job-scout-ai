from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is importable when Streamlit starts from app/
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

from src.auth import get_user_by_id
from src.core.db import initialize_database


def require_user() -> dict:
    initialize_database()
    user_id = st.session_state.get("user_id")
    if not user_id:
        st.warning("Please log in from the Home page.")
        st.page_link("Home.py", label="Go to Home / Login")
        st.stop()
    user = get_user_by_id(user_id)
    if not user:
        st.session_state.clear()
        st.warning("Session expired. Please log in again.")
        st.page_link("Home.py", label="Go to Home / Login")
        st.stop()
    return user
