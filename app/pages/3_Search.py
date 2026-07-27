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
from src.core.config import load_config
from src.search import last_successful_search, next_scheduled_search, run_search
from src.sources import SOURCE_REGISTRY

user = require_user()
st.title("Search")

config = load_config()
enabled = list(SOURCE_REGISTRY.keys())

last = last_successful_search(user["id"])
st.write(f"Last success: `{last['finished_at'] if last else 'never'}`")
st.write(f"Next scheduled: `{next_scheduled_search(user['id']) or 'n/a'}`")

sources = st.multiselect("Job sources", enabled, default=enabled)
location_hint = st.text_input("Location focus (optional filter note)", "")
role_hint = st.text_input("Role focus (optional)", "data analyst")
min_score = st.number_input(
    "Minimum relevance score",
    min_value=0,
    max_value=100,
    value=int(config["search"]["minimum_score"]),
)

progress = st.empty()
if st.button("Search Now", type="primary"):
    progress.info("Searching…")
    try:
        result = run_search(
            user_id=user["id"],
            source_names=sources or None,
            trigger_type="manual",
            minimum_score=int(min_score),
        )
        progress.success(
            f"Done. Fetched {result['fetched']}, matched {result['matched']}, "
            f"new {result['new_count']}."
        )
        if result["errors"]:
            st.warning("Some sources failed:\n" + "\n".join(result["errors"]))
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
        progress.error(f"Search failed: {exc}")

st.caption(f"Hints recorded locally only — role={role_hint!r}, location={location_hint!r}")
