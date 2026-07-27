from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

st.set_page_config(
    page_title="Job Scout AI",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
)

from src.auth import authenticate, create_user, get_user_by_id
from src.core.db import initialize_database
from src.core.logging_setup import setup_logging

setup_logging()
initialize_database()

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.2rem; max-width: 1100px;}
    [data-testid="stSidebar"] {background: linear-gradient(180deg,#0f172a,#1e293b); color:#e2e8f0;}
    [data-testid="stSidebar"] * {color:#e2e8f0 !important;}
    h1,h2,h3 {letter-spacing:-0.02em;}
    </style>
    """,
    unsafe_allow_html=True,
)


def ensure_auth() -> dict | None:
    if "user_id" in st.session_state and st.session_state["user_id"]:
        user = get_user_by_id(st.session_state["user_id"])
        if user:
            return user
    return None


def login_page() -> None:
    st.title("Job Scout AI")
    st.caption("Local multi-user job matching · Hebrew & English · truthful CV tooling")
    tab_login, tab_register = st.tabs(["Log in", "Register"])

    with tab_login:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Log in", type="primary"):
            user = authenticate(email, password)
            if user:
                st.session_state["user_id"] = user["id"]
                st.success("Welcome back.")
                st.rerun()
            else:
                st.error("Invalid email or password.")

    with tab_register:
        email = st.text_input("Email", key="reg_email")
        name = st.text_input("Display name", key="reg_name")
        password = st.text_input("Password (min 8 chars)", type="password", key="reg_password")
        if st.button("Create account"):
            try:
                user = create_user(email, password, name)
                st.session_state["user_id"] = user["id"]
                st.success("Account created.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))


user = ensure_auth()
if not user:
    login_page()
    st.stop()

st.sidebar.title("Job Scout AI")
st.sidebar.write(f"Signed in as **{user.get('display_name') or user['email']}**")
if st.sidebar.button("Log out"):
    st.session_state.clear()
    st.rerun()

st.title(f"Hello, {user.get('display_name') or 'there'}")
st.write(
    "Use the left sidebar pages: **Dashboard**, **CV**, **Search**, **Jobs**, "
    "**Applications**, **Settings**, and **Statistics**."
)
st.page_link("pages/1_Dashboard.py", label="Go to Dashboard", icon="📊")
