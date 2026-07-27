from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

st.set_page_config(
    page_title="Job Scout AI",
    page_icon=str(Path(__file__).resolve().parent / "assets" / "logo.png"),
    layout="wide",
    initial_sidebar_state="expanded",
)

from brand import apply_brand_theme, render_brand_header, render_sidebar_brand
from i18n import language_picker, set_lang, sync_lang_from_prefs, t
from session_cookie import (
    clear_session_cookie,
    init_cookie_manager,
    read_session_cookie,
    write_session_cookie,
)
from src.auth import (
    authenticate,
    create_login_session,
    create_user,
    get_preferences,
    get_user_by_id,
    get_user_by_session_token,
    revoke_session_token,
)
from src.core.config import load_config
from src.core.db import initialize_database
from src.core.logging_setup import setup_logging

setup_logging()
initialize_database()
init_cookie_manager()

if "ui_lang" not in st.session_state:
    set_lang("he")

apply_brand_theme()


def _session_days() -> int:
    configured = int((load_config().get("security") or {}).get("session_days", 1))
    return max(1, configured)


def restore_session_from_cookie() -> dict | None:
    if st.session_state.get("user_id"):
        user = get_user_by_id(st.session_state["user_id"])
        if user:
            return user
        st.session_state.pop("user_id", None)

    token = read_session_cookie()
    user = get_user_by_session_token(token)
    if user:
        st.session_state["user_id"] = user["id"]
        st.session_state["session_token"] = token
        sync_lang_from_prefs(get_preferences(user["id"]))
        return user
    return None


def start_persistent_session(user_id: int) -> None:
    days = _session_days()
    token = create_login_session(user_id, days=days)
    st.session_state["user_id"] = user_id
    st.session_state["session_token"] = token
    write_session_cookie(token, days=days)


def end_persistent_session() -> None:
    token = st.session_state.get("session_token") or read_session_cookie()
    revoke_session_token(token)
    clear_session_cookie()
    st.session_state.clear()
    set_lang("he")


def login_page() -> None:
    # Logo + tagline above the form (branding, not an extra settings window)
    render_brand_header(width=380)
    language_picker("home_lang")
    tab_login, tab_register = st.tabs([t("login"), t("register")])

    with tab_login:
        email = st.text_input(t("email"), key="login_email")
        password = st.text_input(t("password"), type="password", key="login_password")
        if st.button(t("login"), type="primary"):
            user = authenticate(email, password)
            if user:
                start_persistent_session(user["id"])
                sync_lang_from_prefs(get_preferences(user["id"]))
                st.success(t("welcome_back"))
                st.rerun()
            else:
                st.error(t("invalid_credentials"))

    with tab_register:
        email = st.text_input(t("email"), key="reg_email")
        name = st.text_input(t("display_name"), key="reg_name")
        password = st.text_input(t("password_min"), type="password", key="reg_password")
        if st.button(t("create_account"), type="primary"):
            try:
                user = create_user(email, password, name)
                start_persistent_session(user["id"])
                set_lang("he")
                st.success(t("account_created"))
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))


user = restore_session_from_cookie()
if not user:
    login_page()
    st.stop()

render_sidebar_brand()
language_picker("home_lang_authed")
st.sidebar.write(f"{t('signed_in_as')} **{user.get('display_name') or user['email']}**")
if st.sidebar.button(t("log_out")):
    end_persistent_session()
    st.rerun()

render_brand_header(show_caption=False, width=300)
st.title(f"{t('hello')}, {user.get('display_name') or 'there'}")
st.write(t("home_help"))
st.page_link("pages/1_דשבורד.py", label=t("go_dashboard"))
