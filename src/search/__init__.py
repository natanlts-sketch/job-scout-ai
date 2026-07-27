from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.applications import upsert_application
from src.auth import get_preferences
from src.core.config import get_path, load_config
from src.core.db import initialize_database, mark_new_jobs_legacy, upsert_job
from src.core.logging_setup import get_logger, setup_logging
from src.core.models import Job
from src.cv.keywords import extract_keywords
from src.cv.parser import CVParser
from src.cv.upload import get_active_cv, get_user_skills
from src.matching.scorer import add_ats_and_explanation, filter_jobs, score_job
from src.matching.export import export_reports
from src.notify import send_daily_report, send_high_match_alerts
from src.sources import fetch_all_jobs

logger = get_logger("jobscout.search")

LOCK_NAME = "global_search"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def acquire_search_lock(locked_by: str = "cli") -> bool:
    now = _now()
    with initialize_database() as conn:
        row = conn.execute(
            "SELECT locked_at FROM search_locks WHERE lock_name = ?",
            (LOCK_NAME,),
        ).fetchone()
        if row and row["locked_at"]:
            try:
                locked_at = datetime.fromisoformat(row["locked_at"])
                if locked_at.tzinfo is None:
                    locked_at = locked_at.replace(tzinfo=timezone.utc)
                # stale lock after 30 minutes
                if datetime.now(timezone.utc) - locked_at < timedelta(minutes=30):
                    return False
            except ValueError:
                pass
        conn.execute(
            """
            INSERT INTO search_locks (lock_name, locked_by, locked_at)
            VALUES (?, ?, ?)
            ON CONFLICT(lock_name) DO UPDATE SET locked_by=excluded.locked_by, locked_at=excluded.locked_at
            """,
            (LOCK_NAME, locked_by, now),
        )
        conn.commit()
        return True


def release_search_lock() -> None:
    with initialize_database() as conn:
        conn.execute("DELETE FROM search_locks WHERE lock_name = ?", (LOCK_NAME,))
        conn.commit()


def last_successful_search(user_id: int | None = None) -> dict | None:
    with initialize_database() as conn:
        if user_id:
            row = conn.execute(
                """
                SELECT * FROM search_runs
                WHERE status = 'success' AND (user_id = ? OR user_id IS NULL)
                ORDER BY finished_at DESC LIMIT 1
                """,
                (user_id,),
            ).fetchone()
        else:
            row = conn.execute(
                """
                SELECT * FROM search_runs WHERE status = 'success'
                ORDER BY finished_at DESC LIMIT 1
                """
            ).fetchone()
    return dict(row) if row else None


def next_scheduled_search(user_id: int) -> str | None:
    prefs = get_preferences(user_id)
    hours = int(prefs.get("search_frequency_hours") or 24)
    last = last_successful_search(user_id)
    if not last or not last.get("finished_at"):
        return None
    try:
        finished = datetime.fromisoformat(last["finished_at"])
        if finished.tzinfo is None:
            finished = finished.replace(tzinfo=timezone.utc)
        return (finished + timedelta(hours=hours)).isoformat()
    except ValueError:
        return None


def _cv_keywords_for_user(user_id: int | None) -> tuple[list[str], Path | None]:
    config = load_config()
    if user_id:
        skills = get_user_skills(user_id)
        cv = get_active_cv(user_id)
        if skills:
            path = Path(cv["stored_path"]) if cv else None
            return skills, path
        if cv and cv.get("extracted_text"):
            return extract_keywords(cv["extracted_text"]), Path(cv["stored_path"])
    master = get_path("master_cv")
    if master.exists():
        text = CVParser(master).get_text()
        return extract_keywords(text), master
    return [], None


def run_search(
    *,
    user_id: int | None = None,
    source_names: list[str] | None = None,
    trigger_type: str = "manual",
    minimum_score: int | None = None,
) -> dict:
    setup_logging()
    config = load_config()
    locked_by = f"user:{user_id}" if user_id else trigger_type
    if not acquire_search_lock(locked_by):
        raise RuntimeError("A search is already running. Try again shortly.")

    started = _now()
    run_id = None
    try:
        with initialize_database() as conn:
            cur = conn.execute(
                """
                INSERT INTO search_runs (user_id, started_at, status, trigger_type)
                VALUES (?, ?, 'running', ?)
                """,
                (user_id, started, trigger_type),
            )
            run_id = cur.lastrowid
            conn.commit()

        prefs = get_preferences(user_id) if user_id else {}
        preferred_sources = prefs.get("preferred_sources") or source_names
        cv_keywords, _cv_path = _cv_keywords_for_user(user_id)
        logger.info("Starting search (%s). CV keywords: %s", trigger_type, len(cv_keywords))

        jobs, errors = fetch_all_jobs(preferred_sources or source_names, config)
        logger.info("Fetched %s jobs (%s source errors)", len(jobs), len(errors))

        scored: list[Job] = []
        for job in jobs:
            job = score_job(job, config)
            job = add_ats_and_explanation(job, cv_keywords, config)
            scored.append(job)

        filtered = filter_jobs(
            scored,
            config=config,
            minimum_score=minimum_score,
            minimum_ats=float(prefs.get("minimum_ats_score") or 0) or None,
            excluded_companies=prefs.get("excluded_companies") or [],
            excluded_keywords=prefs.get("excluded_keywords") or [],
        )

        now = _now()
        with initialize_database() as conn:
            is_new_map = mark_new_jobs_legacy(conn, [j.job_id for j in filtered], now)
            for job in filtered:
                job.is_new = is_new_map.get(job.job_id, True)
                upsert_job(conn, job.to_dict(), now)
                if user_id:
                    conn.execute(
                        """
                        INSERT INTO job_matches (
                            user_id, job_id, score, ats_score, matched_skills,
                            missing_skills, match_explanation, is_new, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(user_id, job_id) DO UPDATE SET
                            score=excluded.score,
                            ats_score=excluded.ats_score,
                            matched_skills=excluded.matched_skills,
                            missing_skills=excluded.missing_skills,
                            match_explanation=excluded.match_explanation,
                            is_new=excluded.is_new,
                            updated_at=excluded.updated_at
                        """,
                        (
                            user_id,
                            job.job_id,
                            job.score,
                            job.ats_score,
                            job.matched_skills,
                            job.missing_skills,
                            job.match_explanation,
                            1 if job.is_new else 0,
                            now,
                            now,
                        ),
                    )
            conn.commit()

        # Applications after jobs are committed (FK safety across connections)
        if user_id:
            for job in filtered:
                upsert_application(
                    user_id,
                    job,
                    status="New" if job.is_new else "Reviewed",
                )

        new_jobs = [j for j in filtered if j.is_new]
        paths = export_reports(new_jobs, get_path("reports"))

        if user_id:
            threshold = float((config.get("search") or {}).get("high_match_ats_threshold", 70))
            send_daily_report(
                user_id,
                new_jobs,
                notifications_enabled=bool(prefs.get("email_notifications", True)),
            )
            send_high_match_alerts(
                user_id,
                new_jobs,
                threshold,
                notifications_enabled=bool(prefs.get("email_notifications", True)),
            )

        finished = _now()
        with initialize_database() as conn:
            conn.execute(
                """
                UPDATE search_runs SET finished_at=?, status='success',
                    jobs_fetched=?, jobs_matched=?, new_jobs=?,
                    error_message=?
                WHERE id=?
                """,
                (
                    finished,
                    len(jobs),
                    len(filtered),
                    len(new_jobs),
                    "; ".join(errors) if errors else None,
                    run_id,
                ),
            )
            conn.commit()

        logger.info(
            "Search complete: fetched=%s matched=%s new=%s errors=%s",
            len(jobs),
            len(filtered),
            len(new_jobs),
            len(errors),
        )
        return {
            "jobs": filtered,
            "new_jobs": new_jobs,
            "errors": errors,
            "reports": paths,
            "fetched": len(jobs),
            "matched": len(filtered),
            "new_count": len(new_jobs),
            "cv_keywords": cv_keywords,
        }
    except Exception as exc:
        logger.exception("Search failed")
        if run_id:
            with initialize_database() as conn:
                conn.execute(
                    """
                    UPDATE search_runs SET finished_at=?, status='failed', error_message=?
                    WHERE id=?
                    """,
                    (_now(), str(exc), run_id),
                )
                conn.commit()
        raise
    finally:
        release_search_lock()
