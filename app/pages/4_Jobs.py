from __future__ import annotations

from pathlib import Path

import streamlit as st

from auth_gate import require_user
from src.ai import (
    analyze_job,
    generate_cover_letter,
    generate_interview_prep,
    generate_recruiter_message,
)
from src.applications import create_application_package, update_application, upsert_application
from src.auth import get_preferences
from src.core.db import initialize_database
from src.core.models import Job
from src.cv.upload import get_active_cv, get_user_skills
from src.matching.export import filter_frame, sort_jobs

user = require_user()
st.title("Jobs")

prefs = get_preferences(user["id"])

with initialize_database() as conn:
    rows = conn.execute(
        """
        SELECT j.*, m.score, m.ats_score, m.matched_skills, m.missing_skills,
               m.match_explanation, m.is_new
        FROM job_matches m
        JOIN jobs j ON j.job_id = m.job_id
        WHERE m.user_id = ?
        ORDER BY m.ats_score DESC, m.score DESC
        """,
        (user["id"],),
    ).fetchall()

jobs = []
for r in rows:
    job = Job(
        source=r["source"],
        title=r["title"],
        company=r["company"],
        location=r["location"] or "",
        published_at=r["published_at"] or "",
        url=r["url"],
        description=r["description"] or "",
        score=r["score"] or 0,
        ats_score=r["ats_score"] or 0,
        matched_skills=r["matched_skills"] or "",
        missing_skills=r["missing_skills"] or "",
        match_explanation=r["match_explanation"] or "",
        work_type=r["work_type"] or "",
        region=r["region"] or "",
        is_new=bool(r["is_new"]),
        external_id=r["external_id"] or "",
    )
    jobs.append(job)

c1, c2, c3, c4 = st.columns(4)
region = c1.selectbox("Region", ["", "israel_local", "remote", "overseas"])
work_type = c2.selectbox("Work type", ["", "remote", "hybrid", "onsite", "unknown"])
sort_by = c3.selectbox("Sort by", ["ats_score", "score", "date", "company"])
query = c4.text_input("Filter text")

filtered = filter_frame(
    jobs,
    region=region or None,
    work_type=work_type or None,
    query=query or None,
)
filtered = sort_jobs(filtered, by=sort_by, descending=sort_by != "company")

st.write(f"{len(filtered)} jobs")
for job in filtered[:100]:
    badge = "NEW" if job.is_new else ""
    with st.expander(
        f"{badge} {job.title} · {job.company} · ATS {job.ats_score}% · score {job.score}"
    ):
        st.write(job.match_explanation)
        st.write(
            f"Location: {job.location} · {job.work_type} · {job.region} · {job.source}"
        )
        st.write(f"Matched: {job.matched_skills}")
        st.write(f"Missing: {job.missing_skills}")
        st.link_button("Open job", job.url)
        b1, b2, b3, b4, b5 = st.columns(5)
        if b1.button("Save", key=f"save_{job.job_id}"):
            upsert_application(user["id"], job, "Saved")
            st.toast("Saved")
        if b2.button("Reject", key=f"rej_{job.job_id}"):
            upsert_application(user["id"], job, "Rejected")
            st.toast("Rejected")
        if b3.button("Mark applied", key=f"app_{job.job_id}"):
            upsert_application(user["id"], job, "Applied")
            update_application(user["id"], job.job_id, status="Applied")
            st.toast("Marked applied")
        if b4.button("Prepare package", key=f"pkg_{job.job_id}"):
            cv = get_active_cv(user["id"])
            if not cv:
                st.error("Upload a CV first")
            else:
                skills = get_user_skills(user["id"])
                consent = bool(prefs.get("ai_consent"))
                cover = generate_cover_letter(user["id"], job, skills, ai_consent=consent)
                msg = generate_recruiter_message(user["id"], job, ai_consent=consent)
                notes = generate_interview_prep(user["id"], job, ai_consent=consent)
                summary = analyze_job(
                    user["id"],
                    job,
                    cv_text=cv.get("extracted_text") if consent else None,
                    ai_consent=consent,
                )["analysis"]
                folder = create_application_package(
                    user["id"],
                    job,
                    Path(cv["stored_path"]),
                    skills,
                    cover_letter=cover,
                    recruiter_message=msg,
                    interview_notes=notes,
                    job_summary=summary,
                )
                st.success(f"Package ready: {folder}")
        if b5.button("AI explain", key=f"ai_{job.job_id}"):
            consent = bool(prefs.get("ai_consent"))
            cv = get_active_cv(user["id"])
            result = analyze_job(
                user["id"],
                job,
                cv_text=(cv or {}).get("extracted_text") if consent else None,
                ai_consent=consent,
            )
            st.write(result["analysis"])
            st.caption(f"Source: {result['source']}")
