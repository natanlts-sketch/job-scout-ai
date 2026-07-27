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

from src.streamlit_ui.auth_gate import require_user
from src.streamlit_ui.i18n import t
from src.search import last_successful_search, next_scheduled_search
from src.stats import dashboard_stats

user = require_user()
st.title(t("dashboard"))

stats = dashboard_stats(user["id"])
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric(t("jobs_today"), stats["found_today"])
c2.metric(t("new_matches"), stats["new_matches"])
c3.metric(t("applications_sent"), stats["applications_sent"])
c4.metric(t("saved_jobs"), stats["saved_jobs"])
c5.metric(t("avg_ats"), f"{stats['avg_ats']:.1f}%")

best = stats.get("best_match")
st.subheader(t("best_match"))
if best:
    st.write(f"**{best['title']}** {t('at')} {best['company']} — ATS {best['ats_score']}%")
    st.link_button(t("open_job"), best["url"])
else:
    st.info(t("no_matches"))

last = last_successful_search(user["id"])
nxt = next_scheduled_search(user["id"])
st.subheader(t("search_schedule"))
st.write(f"{t('last_success')}: {last['finished_at'] if last else t('never')}")
st.write(f"{t('next_scheduled')}: {nxt or t('not_scheduled')}")
if last and last.get("error_message"):
    st.warning(f"{t('last_run_notes')}: {last['error_message']}")
