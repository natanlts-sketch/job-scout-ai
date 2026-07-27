"""Durable login helpers for Streamlit Cloud (no third-party cookie widgets)."""
from __future__ import annotations

import streamlit as st

PARAM_KEY = "s"


def read_session_token() -> str | None:
    """Read session token from URL param or session_state."""
    token = st.session_state.get("session_token")
    if token:
        return str(token)
    try:
        value = st.query_params.get(PARAM_KEY)
    except Exception:
        value = None
    if isinstance(value, list):
        value = value[0] if value else None
    if not value or value in {"", "null", "None"}:
        return None
    return str(value)


def write_session_token(token: str) -> None:
    st.session_state["session_token"] = token
    try:
        st.query_params[PARAM_KEY] = token
    except Exception:
        pass


def clear_session_token() -> None:
    st.session_state.pop("session_token", None)
    try:
        if PARAM_KEY in st.query_params:
            del st.query_params[PARAM_KEY]
    except Exception:
        try:
            st.query_params.clear()
        except Exception:
            pass


# Backwards-compatible aliases used by older imports
def init_cookie_manager() -> None:
    return None


def read_session_cookie() -> str | None:
    return read_session_token()


def write_session_cookie(token: str, days: int = 1) -> None:
    write_session_token(token)


def clear_session_cookie() -> None:
    clear_session_token()
