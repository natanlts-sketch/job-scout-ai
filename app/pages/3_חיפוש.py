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
from i18n import t
from src.core.config import load_config
from src.search import last_successful_search, next_scheduled_search, run_search
from src.sources import SOURCE_REGISTRY

user = require_user()
st.title(t("search"))

config = load_config()
enabled = list(SOURCE_REGISTRY.keys())

last = last_successful_search(user["id"])
st.write(f"{t('last_success_short')}: `{last['finished_at'] if last else t('never')}`")
st.write(f"{t('next_scheduled_short')}: `{next_scheduled_search(user['id']) or t('not_scheduled')}`")

sources = st.multiselect(t("job_sources"), enabled, default=enabled)
location_hint = st.text_input(t("location_focus"), "")
role_hint = st.text_input(t("role_focus"), "data analyst")
min_score = st.number_input(
    t("min_score"),
    min_value=0,
    max_value=100,
    value=int(config["search"]["minimum_score"]),
)

progress = st.empty()
if st.button(t("search_now"), type="primary"):
    progress.info(t("searching"))
    try:
        result = run_search(
            user_id=user["id"],
            source_names=sources or None,
            trigger_type="manual",
            minimum_score=int(min_score),
        )
        progress.success(
            t(
                "search_done",
                fetched=result["fetched"],
                matched=result["matched"],
                new=result["new_count"],
            )
        )
        if result["errors"]:
            st.warning(t("sources_failed") + "\n" + "\n".join(result["errors"]))
        if result["new_jobs"]:
            st.dataframe(
                [
                    {
                        "title": j.title,
                        "company": j.company,
                        "score": j.score,
                        "ats": j.ats_score,
                        "region": j.region,
                        "new": j.is_new,
                    }
                    for j in result["new_jobs"][:50]
                ]
            )
    except RuntimeError as exc:
        progress.error(str(exc))
    except Exception as exc:  # noqa: BLE001
        progress.error(f"{t('search_failed')}: {exc}")

st.caption(f"role={role_hint!r}, location={location_hint!r}")
