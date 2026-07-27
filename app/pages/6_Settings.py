from __future__ import annotations

import streamlit as st

from auth_gate import require_user
from src.ai import ai_is_enabled
from src.auth import delete_user_and_data, get_preferences, save_preferences
from src.notify import send_test_email
from src.security import PRIVACY_NOTICE, backup_database
from src.sources import SOURCE_REGISTRY

user = require_user()
st.title("Settings")

prefs = get_preferences(user["id"])

st.subheader("Job preferences")
titles = st.text_area(
    "Preferred titles (one per line)",
    value="\n".join(prefs.get("preferred_titles") or []),
)
locations = st.text_area(
    "Preferred locations (one per line)",
    value="\n".join(prefs.get("preferred_locations") or []),
)
remote_preference = st.selectbox(
    "Remote / hybrid / office",
    ["any", "remote", "hybrid", "office"],
    index=["any", "remote", "hybrid", "office"].index(prefs.get("remote_preference") or "any"),
)
min_ats = st.number_input(
    "Minimum ATS score",
    min_value=0.0,
    max_value=100.0,
    value=float(prefs.get("minimum_ats_score") or 0),
)
experience = st.selectbox(
    "Experience level",
    ["junior", "entry", "mid", "intern"],
    index=["junior", "entry", "mid", "intern"].index(prefs.get("experience_level") or "junior")
    if (prefs.get("experience_level") or "junior") in ["junior", "entry", "mid", "intern"]
    else 0,
)
languages = st.multiselect(
    "Preferred languages",
    ["en", "he"],
    default=prefs.get("preferred_languages") or ["en", "he"],
)
excluded_companies = st.text_area(
    "Excluded companies",
    value="\n".join(prefs.get("excluded_companies") or []),
)
excluded_keywords = st.text_area(
    "Excluded keywords",
    value="\n".join(prefs.get("excluded_keywords") or []),
)
preferred_sources = st.multiselect(
    "Preferred job sources",
    list(SOURCE_REGISTRY.keys()),
    default=prefs.get("preferred_sources") or list(SOURCE_REGISTRY.keys()),
)
salary = st.text_input(
    "Salary preference (optional, unused until salary data exists)",
    value=prefs.get("salary_preference") or "",
)
freq = st.number_input(
    "Automatic search frequency (hours)",
    min_value=1,
    max_value=168,
    value=int(prefs.get("search_frequency_hours") or 24),
)
language = st.selectbox("UI language", ["en", "he"], index=0 if prefs.get("language") != "he" else 1)

st.subheader("Notifications & AI")
email_notifications = st.checkbox(
    "Email notifications enabled",
    value=bool(prefs.get("email_notifications", True)),
)
ai_consent = st.checkbox(
    "I consent to sending CV/job text to Anthropic when AI is enabled",
    value=bool(prefs.get("ai_consent", False)),
)
st.caption(f"AI runtime enabled: **{ai_is_enabled()}** (requires AI_ENABLED + ANTHROPIC_API_KEY)")

if st.button("Save preferences", type="primary"):
    save_preferences(
        user["id"],
        {
            "preferred_titles": [t.strip() for t in titles.splitlines() if t.strip()],
            "preferred_locations": [t.strip() for t in locations.splitlines() if t.strip()],
            "remote_preference": remote_preference,
            "minimum_ats_score": min_ats,
            "experience_level": experience,
            "preferred_languages": languages,
            "excluded_companies": [t.strip() for t in excluded_companies.splitlines() if t.strip()],
            "excluded_keywords": [t.strip() for t in excluded_keywords.splitlines() if t.strip()],
            "preferred_sources": preferred_sources,
            "salary_preference": salary or None,
            "email_notifications": email_notifications,
            "ai_consent": ai_consent,
            "search_frequency_hours": int(freq),
            "language": language,
        },
    )
    st.success("Saved")

st.subheader("Email")
if st.button("Send test email"):
    try:
        st.info(send_test_email())
    except Exception as exc:  # noqa: BLE001
        st.error(str(exc))

st.subheader("Privacy & data")
st.markdown(PRIVACY_NOTICE)
if st.button("Backup database now"):
    path = backup_database()
    st.success(f"Backup written to {path}")

st.danger_zone = st.container()
with st.danger_zone:
    st.subheader("Delete account")
    confirm = st.text_input("Type DELETE to confirm account + data removal")
    if st.button("Delete my account and data", type="primary") and confirm == "DELETE":
        delete_user_and_data(user["id"])
        st.session_state.clear()
        st.success("Account deleted.")
        st.page_link("Home.py", label="Back to Home")
