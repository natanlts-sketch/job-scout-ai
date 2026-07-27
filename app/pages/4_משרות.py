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
from i18n import language_picker, t
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
language_picker("jobs_lang")
st.title(t("jobs"))

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
    jobs.append(
        Job(
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
    )

c1, c2, c3, c4 = st.columns(4)
region = c1.selectbox(t("region"), ["", "israel_local", "remote", "overseas"])
work_type = c2.selectbox(t("work_type"), ["", "remote", "hybrid", "onsite", "unknown"])
sort_by = c3.selectbox(t("sort_by"), ["ats_score", "score", "date", "company"])
query = c4.text_input(t("filter_text"))

filtered = filter_frame(
    jobs,
    region=region or None,
    work_type=work_type or None,
    query=query or None,
)
filtered = sort_jobs(filtered, by=sort_by, descending=sort_by != "company")

st.write(t("jobs_count", n=len(filtered)))
for job in filtered[:100]:
    badge = t("new_badge") if job.is_new else ""
    with st.expander(
        f"{badge} {job.title} · {job.company} · ATS {job.ats_score}% · score {job.score}"
    ):
        st.write(job.match_explanation)
        st.write(
            f"{t('location')}: {job.location} · {job.work_type} · {job.region} · {job.source}"
        )
        st.write(f"{t('matched')}: {job.matched_skills}")
        st.write(f"{t('missing')}: {job.missing_skills}")
        st.link_button(t("open_job"), job.url)
        b1, b2, b3, b4, b5 = st.columns(5)
        if b1.button(t("save"), key=f"save_{job.job_id}"):
            upsert_application(user["id"], job, "Saved")
            st.toast(t("saved"))
        if b2.button(t("reject"), key=f"rej_{job.job_id}"):
            upsert_application(user["id"], job, "Rejected")
            st.toast(t("reject"))
        if b3.button(t("mark_applied"), key=f"app_{job.job_id}"):
            upsert_application(user["id"], job, "Applied")
            update_application(user["id"], job.job_id, status="Applied")
            st.toast(t("mark_applied"))
        if b4.button(t("prepare_package"), key=f"pkg_{job.job_id}"):
            cv = get_active_cv(user["id"])
            if not cv:
                st.error(t("upload_cv_first"))
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
                st.success(f"{t('package_ready')}: {folder}")
        if b5.button(t("ai_explain"), key=f"ai_{job.job_id}"):
            consent = bool(prefs.get("ai_consent"))
            cv = get_active_cv(user["id"])
            result = analyze_job(
                user["id"],
                job,
                cv_text=(cv or {}).get("extracted_text") if consent else None,
                ai_consent=consent,
            )
            st.write(result["analysis"])
            st.caption(f"{t('source')}: {result['source']}")
