from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
_APP = Path(__file__).resolve().parents[1]
if str(_APP) not in sys.path:
    sys.path.insert(0, str(_APP))

import pandas as pd
import streamlit as st

from auth_gate import require_user
from src.stats import dashboard_stats

user = require_user()
st.title("Statistics")

stats = dashboard_stats(user["id"])
rates = stats["rates"]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Applied", rates["applied"])
c2.metric("Interviews", rates["interviews"])
c3.metric("Response rate %", rates["response_rate"])
c4.metric("Success rate %", rates["success_rate"])

st.subheader("Jobs found per day")
df_day = pd.DataFrame(stats["jobs_per_day"])
if not df_day.empty:
    st.bar_chart(df_day.set_index("day")["count"])
else:
    st.info("No daily job data yet.")

st.subheader("Local vs remote vs overseas")
df_region = pd.DataFrame(stats["by_region"])
if not df_region.empty:
    st.bar_chart(df_region.set_index("label")["count"])

st.subheader("Jobs by source")
df_source = pd.DataFrame(stats["by_source"])
if not df_source.empty:
    st.bar_chart(df_source.set_index("label")["count"])

st.subheader("Highest-matching skills")
df_m = pd.DataFrame(stats["top_matched_skills"])
if not df_m.empty:
    st.bar_chart(df_m.set_index("skill")["count"])

st.subheader("Most frequently missing skills")
df_x = pd.DataFrame(stats["top_missing_skills"])
if not df_x.empty:
    st.bar_chart(df_x.set_index("skill")["count"])

st.subheader("Status funnel")
df_f = pd.DataFrame(stats["funnel"])
if not df_f.empty:
    st.bar_chart(df_f.set_index("status")["count"])
else:
    st.info("No application funnel data yet.")

st.caption(f"Companies applied to: {rates.get('companies_applied', 0)}")
