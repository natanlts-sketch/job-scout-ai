from __future__ import annotations

import streamlit as st

from auth_gate import require_user
from src.applications import list_applications, mark_package_approved_and_applied, update_application
from src.core.models import APPLICATION_STATUSES

user = require_user()
st.title("Applications")

status_filter = st.selectbox("Status filter", ["(all)"] + APPLICATION_STATUSES)
apps = list_applications(
    user["id"],
    None if status_filter == "(all)" else status_filter,
)

st.write(f"{len(apps)} applications")
for app in apps:
    with st.expander(f"{app['status']} · {app['title']} · {app['company']}"):
        st.write(f"Source: {app['source']} · Location: {app.get('location')}")
        st.link_button("Open job", app["url"])
        st.write(f"Package: {app.get('package_path') or '—'}")
        new_status = st.selectbox(
            "Update status",
            APPLICATION_STATUSES,
            index=APPLICATION_STATUSES.index(app["status"])
            if app["status"] in APPLICATION_STATUSES
            else 0,
            key=f"st_{app['id']}",
        )
        notes = st.text_area("Notes", value=app.get("notes") or "", key=f"notes_{app['id']}")
        recruiter = st.text_input(
            "Recruiter",
            value=app.get("recruiter_name") or "",
            key=f"rec_{app['id']}",
        )
        follow_up = st.text_input(
            "Follow-up date",
            value=app.get("follow_up_date") or "",
            key=f"fu_{app['id']}",
        )
        interview = st.text_input(
            "Interview date",
            value=app.get("interview_date") or "",
            key=f"iv_{app['id']}",
        )
        outcome = st.text_input(
            "Final outcome",
            value=app.get("final_outcome") or "",
            key=f"out_{app['id']}",
        )
        c1, c2 = st.columns(2)
        if c1.button("Save changes", key=f"saveapp_{app['id']}"):
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
            st.success("Updated")
            st.rerun()
        if app.get("package_path") and c2.button(
            "Approve package → Applied",
            key=f"approve_{app['id']}",
        ):
            mark_package_approved_and_applied(user["id"], app["job_id"])
            st.success("Marked Applied (manual submission still required on the job site)")
            st.rerun()
