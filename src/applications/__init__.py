from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from src.core.config import get_path
from src.core.db import initialize_database, upsert_job
from src.core.logging_setup import get_logger
from src.core.models import APPLICATION_STATUSES, Job
from src.core.text import safe_filename
from src.cv.generator import generate_tailored_cvs
from src.cv.keywords import extract_keywords
from src.cv.parser import CVParser
from src.cv.tailor import export_pdf_from_docx

logger = get_logger("jobscout.applications")


def upsert_application(user_id: int, job: Job, status: str = "New") -> int:
    if status not in APPLICATION_STATUSES:
        raise ValueError(f"Invalid status: {status}")
    now = datetime.now(timezone.utc).isoformat()
    with initialize_database() as conn:
        upsert_job(conn, job.to_dict(), now)
        existing = conn.execute(
            "SELECT id FROM applications WHERE user_id = ? AND job_id = ?",
            (user_id, job.job_id),
        ).fetchone()
        if existing:
            conn.execute(
                """
                UPDATE applications SET status = ?, updated_at = ?
                WHERE id = ?
                """,
                (status, now, existing["id"]),
            )
            conn.commit()
            return existing["id"]
        cur = conn.execute(
            """
            INSERT INTO applications (
                user_id, job_id, status, date_found, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, job.job_id, status, now, now, now),
        )
        conn.commit()
        return cur.lastrowid


def update_application(user_id: int, job_id: str, **fields) -> None:
    allowed = {
        "status",
        "date_applied",
        "cv_version",
        "cover_letter_path",
        "package_path",
        "recruiter_name",
        "interview_date",
        "notes",
        "follow_up_date",
        "final_outcome",
    }
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return
    now = datetime.now(timezone.utc).isoformat()
    updates["updated_at"] = now
    if updates.get("status") == "Applied" and "date_applied" not in updates:
        updates["date_applied"] = now
    columns = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [user_id, job_id]
    with initialize_database() as conn:
        conn.execute(
            f"UPDATE applications SET {columns} WHERE user_id = ? AND job_id = ?",
            values,
        )
        conn.commit()


def list_applications(user_id: int, status: str | None = None) -> list[dict]:
    with initialize_database() as conn:
        if status:
            rows = conn.execute(
                """
                SELECT a.*, j.title, j.company, j.url, j.location, j.source
                FROM applications a
                JOIN jobs j ON j.job_id = a.job_id
                WHERE a.user_id = ? AND a.status = ?
                ORDER BY a.updated_at DESC
                """,
                (user_id, status),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT a.*, j.title, j.company, j.url, j.location, j.source
                FROM applications a
                JOIN jobs j ON j.job_id = a.job_id
                WHERE a.user_id = ?
                ORDER BY a.updated_at DESC
                """,
                (user_id,),
            ).fetchall()
    return [dict(r) for r in rows]


def create_application_package(
    user_id: int,
    job: Job,
    cv_path: Path,
    cv_keywords: list[str],
    *,
    cover_letter: str = "",
    recruiter_message: str = "",
    interview_notes: str = "",
    job_summary: str = "",
) -> Path:
    """One-click application package (no auto-submit)."""
    base = get_path("applications") / str(user_id)
    stamp = datetime.now().strftime("%Y-%m-%d")
    folder_name = f"{safe_filename(job.company)}_{safe_filename(job.title)}_{stamp}"
    folder = base / folder_name
    folder.mkdir(parents=True, exist_ok=True)

    tailored_paths = generate_tailored_cvs(
        jobs=[job],
        master_cv_path=cv_path,
        output_directory=folder,
        cv_keywords=cv_keywords,
        also_pdf=True,
    )
    tailored = tailored_paths[0]
    pdf_sibling = tailored.with_suffix(".pdf")
    target_docx = folder / "tailored_cv.docx"
    target_pdf = folder / "tailored_cv.pdf"
    if tailored.resolve() != target_docx.resolve():
        target_docx.write_bytes(tailored.read_bytes())
        tailored.unlink(missing_ok=True)
    if pdf_sibling.exists():
        target_pdf.write_bytes(pdf_sibling.read_bytes())
        if pdf_sibling.resolve() != target_pdf.resolve():
            pdf_sibling.unlink(missing_ok=True)
    elif not target_pdf.exists():
        export_pdf_from_docx(target_docx, target_pdf)

    (folder / "job_description.txt").write_text(
        f"Title: {job.title}\nCompany: {job.company}\nURL: {job.url}\n\n"
        f"{job_summary or job.description}\n",
        encoding="utf-8",
    )
    (folder / "match_explanation.txt").write_text(
        f"Score: {job.score}\nATS: {job.ats_score}\n"
        f"Matched: {job.matched_skills}\nMissing: {job.missing_skills}\n\n"
        f"{job.match_explanation}\n",
        encoding="utf-8",
    )
    (folder / "missing_skills.txt").write_text(job.missing_skills or "None", encoding="utf-8")
    (folder / "cover_letter.txt").write_text(
        cover_letter
        or (
            f"Dear Hiring Team,\n\nI am applying for the {job.title} role at {job.company}. "
            f"My background aligns with: {job.matched_skills or 'data analysis'}.\n\n"
            f"Best regards\n"
        ),
        encoding="utf-8",
    )
    (folder / "recruiter_message.txt").write_text(
        recruiter_message
        or f"Hi — interested in the {job.title} role at {job.company}. Happy to share my CV.",
        encoding="utf-8",
    )
    (folder / "interview_notes.txt").write_text(
        interview_notes
        or (
            f"Prepare examples using: {job.matched_skills}\n"
            f"Be ready to discuss gaps: {job.missing_skills}\n"
            f"Review JD: {job.url}\n"
        ),
        encoding="utf-8",
    )
    (folder / "source_link.txt").write_text(job.url, encoding="utf-8")

    upsert_application(user_id, job, status="Preparing")
    update_application(
        user_id,
        job.job_id,
        status="Preparing",
        package_path=str(folder),
        cv_version=str(target_docx),
        cover_letter_path=str(folder / "cover_letter.txt"),
    )
    logger.info("Created application package at %s", folder)
    return folder


def mark_package_approved_and_applied(user_id: int, job_id: str) -> None:
    """User approval step before marking as Applied (manual apply elsewhere)."""
    update_application(user_id, job_id, status="Applied")
