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
from i18n import t
from src.stats import dashboard_stats

user = require_user()
st.title(t("statistics"))

stats = dashboard_stats(user["id"])
rates = stats["rates"]

c1, c2, c3, c4 = st.columns(4)
c1.metric(t("applied"), rates["applied"])
c2.metric(t("interviews"), rates["interviews"])
c3.metric(t("response_rate"), rates["response_rate"])
c4.metric(t("success_rate"), rates["success_rate"])

st.subheader(t("jobs_per_day"))
df_day = pd.DataFrame(stats["jobs_per_day"])
if not df_day.empty:
    st.bar_chart(df_day.set_index("day")["count"])
else:
    st.info(t("no_daily"))

st.subheader(t("local_remote_overseas"))
df_region = pd.DataFrame(stats["by_region"])
if not df_region.empty:
    st.bar_chart(df_region.set_index("label")["count"])

st.subheader(t("jobs_by_source"))
df_source = pd.DataFrame(stats["by_source"])
if not df_source.empty:
    st.bar_chart(df_source.set_index("label")["count"])

st.subheader(t("top_matched_skills"))
df_m = pd.DataFrame(stats["top_matched_skills"])
if not df_m.empty:
    st.bar_chart(df_m.set_index("skill")["count"])

st.subheader(t("top_missing_skills"))
df_x = pd.DataFrame(stats["top_missing_skills"])
if not df_x.empty:
    st.bar_chart(df_x.set_index("skill")["count"])

st.subheader(t("status_funnel"))
df_f = pd.DataFrame(stats["funnel"])
if not df_f.empty:
    st.bar_chart(df_f.set_index("status")["count"])
else:
    st.info(t("no_funnel"))

st.caption(f"{t('companies_applied')}: {rates.get('companies_applied', 0)}")
