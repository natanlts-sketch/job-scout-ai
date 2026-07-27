"""Browser cookie helpers for durable Streamlit login sessions."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import streamlit as st

COOKIE_KEY = "jobscout_session"
_MANAGER = None


def init_cookie_manager():
    """Create CookieManager once per script run (Streamlit keys must be unique)."""
    global _MANAGER
    if _MANAGER is None:
        import extra_streamlit_components as stx

        _MANAGER = stx.CookieManager(key="jobscout_cookie_manager")
    return _MANAGER


def read_session_cookie() -> str | None:
    manager = init_cookie_manager()
    value = manager.get(COOKIE_KEY)
    # Allow one hydration pass for the cookie component.
    if not st.session_state.get("_cookies_hydrated"):
        st.session_state["_cookies_hydrated"] = True
        if value is None:
            st.rerun()
    if not value or value in {"", "null", "None"}:
        return None
    return str(value)


def write_session_cookie(token: str, days: int = 1) -> None:
    manager = init_cookie_manager()
    expires = datetime.now(timezone.utc) + timedelta(days=max(1, days))
    manager.set(
        COOKIE_KEY,
        token,
        expires_at=expires,
    )


def clear_session_cookie() -> None:
    manager = init_cookie_manager()
    manager.delete(COOKIE_KEY)
