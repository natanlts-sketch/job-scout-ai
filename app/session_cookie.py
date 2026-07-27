"""Browser cookie helpers for durable Streamlit login sessions."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import streamlit as st

COOKIE_KEY = "jobscout_session"


def _cookie_manager():
    import extra_streamlit_components as stx

    # Unique key so the component mounts once per app session.
    return stx.CookieManager(key="jobscout_cookie_manager")


def read_session_cookie() -> str | None:
    manager = _cookie_manager()
    value = manager.get(COOKIE_KEY)
    # First render often returns None before the component hydrates.
    if value is None and not st.session_state.get("_cookies_ready"):
        st.session_state["_cookies_ready"] = True
        st.rerun()
    if not value or value in {"", "null", "None"}:
        return None
    return str(value)


def write_session_cookie(token: str, days: int = 1) -> None:
    manager = _cookie_manager()
    expires = datetime.now(timezone.utc) + timedelta(days=max(1, days))
    manager.set(
        COOKIE_KEY,
        token,
        expires_at=expires,
    )


def clear_session_cookie() -> None:
    manager = _cookie_manager()
    manager.delete(COOKIE_KEY)
