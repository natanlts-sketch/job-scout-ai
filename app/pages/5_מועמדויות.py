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
from src.applications import list_applications, mark_package_approved_and_applied, update_application
from src.core.models import APPLICATION_STATUSES

user = require_user()
st.title(t("applications"))

status_filter = st.selectbox(t("status_filter"), [t("all")] + APPLICATION_STATUSES)
apps = list_applications(
    user["id"],
    None if status_filter == t("all") else status_filter,
)

st.write(t("apps_count", n=len(apps)))
for app in apps:
    with st.expander(f"{app['status']} · {app['title']} · {app['company']}"):
        st.write(f"{t('source')}: {app['source']} · {t('location')}: {app.get('location')}")
        st.link_button(t("open_job"), app["url"])
        st.write(f"{t('package')}: {app.get('package_path') or '—'}")
        new_status = st.selectbox(
            t("update_status"),
            APPLICATION_STATUSES,
            index=APPLICATION_STATUSES.index(app["status"])
            if app["status"] in APPLICATION_STATUSES
            else 0,
            key=f"st_{app['id']}",
        )
        notes = st.text_area(t("notes"), value=app.get("notes") or "", key=f"notes_{app['id']}")
        recruiter = st.text_input(
            t("recruiter"),
            value=app.get("recruiter_name") or "",
            key=f"rec_{app['id']}",
        )
        follow_up = st.text_input(
            t("follow_up"),
            value=app.get("follow_up_date") or "",
            key=f"fu_{app['id']}",
        )
        interview = st.text_input(
            t("interview_date"),
            value=app.get("interview_date") or "",
            key=f"iv_{app['id']}",
        )
        outcome = st.text_input(
            t("final_outcome"),
            value=app.get("final_outcome") or "",
            key=f"out_{app['id']}",
        )
        c1, c2 = st.columns(2)
        if c1.button(t("save_changes"), key=f"saveapp_{app['id']}"):
            update_application(
                user["id"],
                app["job_id"],
                status=new_status,
                notes=notes,
                recruiter_name=recruiter,
                follow_up_date=follow_up,
                interview_date=interview,
                final_outcome=outcome,
            )
            st.success(t("updated"))
            st.rerun()
        if app.get("package_path") and c2.button(
            t("approve_applied"),
            key=f"approve_{app['id']}",
        ):
            mark_package_approved_and_applied(user["id"], app["job_id"])
            st.success(t("marked_applied"))
            st.rerun()
