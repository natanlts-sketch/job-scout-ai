from __future__ import annotations

import streamlit as st

from auth_gate import require_user
from src.search import last_successful_search, next_scheduled_search
from src.stats import dashboard_stats

user = require_user()
st.title("Dashboard")

stats = dashboard_stats(user["id"])
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Jobs found today", stats["found_today"])
c2.metric("New matches", stats["new_matches"])
c3.metric("Applications sent", stats["applications_sent"])
c4.metric("Saved jobs", stats["saved_jobs"])
c5.metric("Avg ATS", f"{stats['avg_ats']:.1f}%")

best = stats.get("best_match")
st.subheader("Best match")
if best:
    st.write(f"**{best['title']}** at {best['company']} — ATS {best['ats_score']}%")
    st.link_button("Open job", best["url"])
else:
    st.info("No matches yet. Run a search.")

last = last_successful_search(user["id"])
nxt = next_scheduled_search(user["id"])
st.subheader("Search schedule")
st.write(f"Last successful search: {last['finished_at'] if last else 'Never'}")
st.write(f"Next scheduled (estimate): {nxt or 'Not scheduled yet'}")
if last and last.get("error_message"):
    st.warning(f"Last run notes: {last['error_message']}")
