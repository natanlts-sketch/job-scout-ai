from __future__ import annotations

import os
import re
from pathlib import Path

from src.core.config import get_path, load_config
from src.core.db import initialize_database
from src.core.logging_setup import get_logger
from src.core.text import safe_filename
from src.cv.keywords import extract_keywords
from src.cv.parser import CVParser, extract_cv_sections
from src.matching.skills import normalize_skills

logger = get_logger("jobscout.cv.upload")


def validate_upload(filename: str, size_bytes: int) -> None:
    config = load_config()
    security = config.get("security", {})
    max_mb = int(security.get("max_upload_mb", 5))
    allowed = set(security.get("allowed_cv_extensions", [".docx", ".pdf"]))
    ext = Path(filename).suffix.lower()
    if ext not in allowed:
        raise ValueError(f"Unsupported file type {ext}. Allowed: {', '.join(sorted(allowed))}")
    if size_bytes > max_mb * 1024 * 1024:
        raise ValueError(f"File too large. Max {max_mb} MB")
    # Block path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise ValueError("Invalid filename")


def store_cv_upload(user_id: int, filename: str, raw_bytes: bytes) -> dict:
    validate_upload(filename, len(raw_bytes))
    uploads = get_path("uploads") / str(user_id)
    uploads.mkdir(parents=True, exist_ok=True)

    safe_name = safe_filename(Path(filename).stem) + Path(filename).suffix.lower()
    stored = uploads / safe_name
    stored.write_bytes(raw_bytes)

    parse_status = "success"
    parse_error = None
    text = ""
    sections: dict = {}
    try:
        parser = CVParser(stored)
        text = parser.get_text()
        sections = extract_cv_sections(text)
        if not text.strip():
            parse_status = "failed"
            parse_error = "No text extracted from CV"
    except Exception as exc:  # noqa: BLE001
        parse_status = "failed"
        parse_error = str(exc)
        logger.error("CV parse failed for user %s: %s", user_id, exc)

    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).isoformat()
    with initialize_database() as conn:
        # deactivate previous
        conn.execute(
            "UPDATE cvs SET is_active = 0, updated_at = ? WHERE user_id = ?",
            (now, user_id),
        )
        cur = conn.execute(
            """
            INSERT INTO cvs (
                user_id, filename, stored_path, extracted_text, parse_status,
                parse_error, created_at, updated_at, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (user_id, safe_name, str(stored), text, parse_status, parse_error, now, now),
        )
        cv_id = cur.lastrowid

        # Replace extracted skills
        conn.execute("DELETE FROM skills WHERE user_id = ? AND source = 'extracted'", (user_id,))
        keywords = normalize_skills(extract_keywords(text)) if text else []
        for skill in keywords:
            conn.execute(
                """
                INSERT OR IGNORE INTO skills (user_id, cv_id, skill_name, source)
                VALUES (?, ?, ?, 'extracted')
                """,
                (user_id, cv_id, skill),
            )
        conn.commit()

    return {
        "cv_id": cv_id,
        "filename": safe_name,
        "path": str(stored),
        "parse_status": parse_status,
        "parse_error": parse_error,
        "sections": sections,
        "skills": keywords if text else [],
    }


def get_active_cv(user_id: int) -> dict | None:
    with initialize_database() as conn:
        row = conn.execute(
            "SELECT * FROM cvs WHERE user_id = ? AND is_active = 1 ORDER BY id DESC LIMIT 1",
            (user_id,),
        ).fetchone()
    return dict(row) if row else None


def get_user_skills(user_id: int) -> list[str]:
    with initialize_database() as conn:
        rows = conn.execute(
            "SELECT skill_name FROM skills WHERE user_id = ? ORDER BY skill_name",
            (user_id,),
        ).fetchall()
    return [r["skill_name"] for r in rows]


def add_user_skill(user_id: int, skill: str) -> None:
    skill = skill.strip().lower()
    if not skill:
        return
    with initialize_database() as conn:
        cv = conn.execute(
            "SELECT id FROM cvs WHERE user_id = ? AND is_active = 1 LIMIT 1",
            (user_id,),
        ).fetchone()
        cv_id = cv["id"] if cv else None
        conn.execute(
            """
            INSERT OR IGNORE INTO skills (user_id, cv_id, skill_name, source)
            VALUES (?, ?, ?, 'manual')
            """,
            (user_id, cv_id, skill),
        )
        conn.commit()


def remove_user_skill(user_id: int, skill: str) -> None:
    with initialize_database() as conn:
        conn.execute(
            "DELETE FROM skills WHERE user_id = ? AND skill_name = ?",
            (user_id, skill.strip().lower()),
        )
        conn.commit()


def delete_active_cv(user_id: int) -> None:
    cv = get_active_cv(user_id)
    if not cv:
        return
    path = Path(cv["stored_path"])
    if path.exists():
        path.unlink()
    with initialize_database() as conn:
        conn.execute("DELETE FROM cvs WHERE id = ?", (cv["id"],))
        conn.execute("DELETE FROM skills WHERE user_id = ? AND source = 'extracted'", (user_id,))
        conn.commit()
