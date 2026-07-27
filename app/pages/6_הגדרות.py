from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
_APP = Path(__file__).resolve().parents[1]
if str(_APP) not in sys.path:
    sys.path.insert(0, str(_APP))

import streamlit as st

from auth_gate import require_user
from i18n import language_picker, set_lang, t
from src.ai import ai_is_enabled
from src.auth import delete_user_and_data, get_preferences, save_preferences
from src.notify import send_test_email
from src.security import PRIVACY_NOTICE, backup_database
from src.sources import SOURCE_REGISTRY

user = require_user()
language_picker("settings_lang")
st.title(t("settings"))

prefs = get_preferences(user["id"])

st.subheader(t("job_prefs"))
titles = st.text_area(
    t("preferred_titles"),
    value="\n".join(prefs.get("preferred_titles") or []),
)
locations = st.text_area(
    t("preferred_locations"),
    value="\n".join(prefs.get("preferred_locations") or []),
)
remote_preference = st.selectbox(
    t("remote_pref"),
    ["any", "remote", "hybrid", "office"],
    index=["any", "remote", "hybrid", "office"].index(prefs.get("remote_preference") or "any"),
)
min_ats = st.number_input(
    t("min_ats"),
    min_value=0.0,
    max_value=100.0,
    value=float(prefs.get("minimum_ats_score") or 0),
)
experience = st.selectbox(
    t("experience"),
    ["junior", "entry", "mid", "intern"],
    index=["junior", "entry", "mid", "intern"].index(prefs.get("experience_level") or "junior")
    if (prefs.get("experience_level") or "junior") in ["junior", "entry", "mid", "intern"]
    else 0,
)
languages = st.multiselect(
    t("preferred_langs"),
    ["en", "he"],
    default=prefs.get("preferred_languages") or ["en", "he"],
)
excluded_companies = st.text_area(
    t("excluded_companies"),
    value="\n".join(prefs.get("excluded_companies") or []),
)
excluded_keywords = st.text_area(
    t("excluded_keywords"),
    value="\n".join(prefs.get("excluded_keywords") or []),
)
preferred_sources = st.multiselect(
    t("preferred_sources"),
    list(SOURCE_REGISTRY.keys()),
    default=prefs.get("preferred_sources") or list(SOURCE_REGISTRY.keys()),
)
salary = st.text_input(
    t("salary_pref"),
    value=prefs.get("salary_preference") or "",
)
freq = st.number_input(
    t("search_freq"),
    min_value=1,
    max_value=168,
    value=int(prefs.get("search_frequency_hours") or 24),
)
language = st.selectbox(
    t("ui_language"),
    ["he", "en"],
    index=0 if (prefs.get("language") or "he") != "en" else 1,
)

st.subheader(t("notifications_ai"))
email_notifications = st.checkbox(
    t("email_notifications"),
    value=bool(prefs.get("email_notifications", True)),
)
ai_consent = st.checkbox(
    t("ai_consent"),
    value=bool(prefs.get("ai_consent", False)),
)
st.caption(f"{t('ai_runtime')}: **{ai_is_enabled()}** (AI_ENABLED + ANTHROPIC_API_KEY)")

if st.button(t("save_prefs"), type="primary"):
    save_preferences(
        user["id"],
        {
            "preferred_titles": [x.strip() for x in titles.splitlines() if x.strip()],
            "preferred_locations": [x.strip() for x in locations.splitlines() if x.strip()],
            "remote_preference": remote_preference,
            "minimum_ats_score": min_ats,
            "experience_level": experience,
            "preferred_languages": languages,
            "excluded_companies": [x.strip() for x in excluded_companies.splitlines() if x.strip()],
            "excluded_keywords": [x.strip() for x in excluded_keywords.splitlines() if x.strip()],
            "preferred_sources": preferred_sources,
            "salary_preference": salary or None,
            "email_notifications": email_notifications,
            "ai_consent": ai_consent,
            "search_frequency_hours": int(freq),
            "language": language,
        },
    )
    set_lang(language)
    st.success(t("saved"))
    st.rerun()

st.subheader(t("email"))
if st.button(t("test_email")):
    try:
        st.info(send_test_email())
    except Exception as exc:  # noqa: BLE001
        st.error(str(exc))

st.subheader(t("privacy_data"))
st.markdown(PRIVACY_NOTICE)
if st.button(t("backup_now")):
    path = backup_database()
    st.success(t("backup_written", path=path))

st.subheader(t("delete_account"))
confirm = st.text_input(t("type_delete"))
if st.button(t("delete_my_account"), type="primary") and confirm == "DELETE":
    delete_user_and_data(user["id"])
    st.session_state.clear()
    st.success(t("account_deleted"))
    st.page_link("Home.py", label=t("back_home"))
