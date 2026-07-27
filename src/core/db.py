from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Iterable

from src.core.config import get_path, load_config
from src.core.logging_setup import get_logger

logger = get_logger("jobscout.db")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    display_name TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS cvs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    stored_path TEXT NOT NULL,
    extracted_text TEXT,
    parse_status TEXT NOT NULL DEFAULT 'pending',
    parse_error TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    cv_id INTEGER REFERENCES cvs(id) ON DELETE SET NULL,
    skill_name TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'extracted',
    UNIQUE(user_id, skill_name)
);

CREATE TABLE IF NOT EXISTS user_preferences (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    preferred_titles TEXT DEFAULT '[]',
    preferred_locations TEXT DEFAULT '[]',
    remote_preference TEXT DEFAULT 'any',
    minimum_ats_score REAL DEFAULT 0,
    experience_level TEXT DEFAULT 'junior',
    preferred_languages TEXT DEFAULT '["en","he"]',
    excluded_companies TEXT DEFAULT '[]',
    excluded_keywords TEXT DEFAULT '[]',
    preferred_sources TEXT DEFAULT '[]',
    salary_preference TEXT,
    email_notifications INTEGER DEFAULT 1,
    ai_consent INTEGER DEFAULT 0,
    search_frequency_hours INTEGER DEFAULT 24,
    language TEXT DEFAULT 'he',
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT,
    published_at TEXT,
    url TEXT NOT NULL,
    description TEXT,
    work_type TEXT,
    region TEXT,
    external_id TEXT,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS job_matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_id TEXT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    score INTEGER DEFAULT 0,
    ats_score REAL DEFAULT 0,
    matched_skills TEXT,
    missing_skills TEXT,
    match_explanation TEXT,
    is_new INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(user_id, job_id)
);

CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_id TEXT NOT NULL REFERENCES jobs(job_id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'New',
    date_found TEXT,
    date_applied TEXT,
    cv_version TEXT,
    cover_letter_path TEXT,
    package_path TEXT,
    recruiter_name TEXT,
    interview_date TEXT,
    notes TEXT,
    follow_up_date TEXT,
    final_outcome TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(user_id, job_id)
);

CREATE TABLE IF NOT EXISTS generated_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_id TEXT REFERENCES jobs(job_id) ON DELETE SET NULL,
    doc_type TEXT NOT NULL,
    file_path TEXT NOT NULL,
    approved INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS search_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL,
    jobs_fetched INTEGER DEFAULT 0,
    jobs_matched INTEGER DEFAULT 0,
    new_jobs INTEGER DEFAULT 0,
    error_message TEXT,
    trigger_type TEXT DEFAULT 'manual'
);

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_id TEXT REFERENCES jobs(job_id) ON DELETE SET NULL,
    channel TEXT NOT NULL,
    kind TEXT NOT NULL,
    sent_at TEXT NOT NULL,
    UNIQUE(user_id, job_id, kind)
);

CREATE TABLE IF NOT EXISTS ai_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    job_id TEXT NOT NULL,
    feature TEXT NOT NULL,
    response_text TEXT NOT NULL,
    tokens_used INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    UNIQUE(user_id, job_id, feature)
);

CREATE TABLE IF NOT EXISTS ai_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    day TEXT NOT NULL,
    tokens_used INTEGER DEFAULT 0,
    UNIQUE(user_id, day)
);

CREATE TABLE IF NOT EXISTS seen_jobs (
    job_id TEXT PRIMARY KEY,
    first_seen TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS search_locks (
    lock_name TEXT PRIMARY KEY,
    locked_by TEXT,
    locked_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source);
CREATE INDEX IF NOT EXISTS idx_jobs_region ON jobs(region);
CREATE INDEX IF NOT EXISTS idx_job_matches_user ON job_matches(user_id);
CREATE INDEX IF NOT EXISTS idx_applications_user_status ON applications(user_id, status);
CREATE INDEX IF NOT EXISTS idx_search_runs_user ON search_runs(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id);
"""


def get_db_path() -> Path:
    try:
        return get_path("database")
    except Exception:
        return Path("data/jobs.db")


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(path), check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(db_path: Path | None = None) -> sqlite3.Connection:
    connection = connect(db_path)
    connection.executescript(SCHEMA_SQL)
    connection.commit()
    logger.info("Database initialized at %s", db_path or get_db_path())
    return connection


@contextmanager
def db_session(db_path: Path | None = None) -> Generator[sqlite3.Connection, None, None]:
    connection = initialize_database(db_path)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def upsert_job(connection: sqlite3.Connection, job_dict: dict, now: str) -> None:
    existing = connection.execute(
        "SELECT job_id FROM jobs WHERE job_id = ?",
        (job_dict["job_id"],),
    ).fetchone()

    if existing:
        connection.execute(
            """
            UPDATE jobs SET
                title=?, company=?, location=?, published_at=?, url=?,
                description=?, work_type=?, region=?, external_id=?,
                last_seen=?, updated_at=?
            WHERE job_id=?
            """,
            (
                job_dict["title"],
                job_dict["company"],
                job_dict.get("location", ""),
                job_dict.get("published_at", ""),
                job_dict["url"],
                job_dict.get("description", ""),
                job_dict.get("work_type", ""),
                job_dict.get("region", ""),
                job_dict.get("external_id", ""),
                now,
                now,
                job_dict["job_id"],
            ),
        )
    else:
        connection.execute(
            """
            INSERT INTO jobs (
                job_id, source, title, company, location, published_at, url,
                description, work_type, region, external_id,
                first_seen, last_seen, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_dict["job_id"],
                job_dict["source"],
                job_dict["title"],
                job_dict["company"],
                job_dict.get("location", ""),
                job_dict.get("published_at", ""),
                job_dict["url"],
                job_dict.get("description", ""),
                job_dict.get("work_type", ""),
                job_dict.get("region", ""),
                job_dict.get("external_id", ""),
                now,
                now,
                now,
                now,
            ),
        )


def mark_new_jobs_legacy(connection: sqlite3.Connection, job_ids: Iterable[str], now: str) -> dict[str, bool]:
    """Legacy seen_jobs table used by CLI pipeline; returns is_new map."""
    result: dict[str, bool] = {}
    for job_id in job_ids:
        exists = connection.execute(
            "SELECT 1 FROM seen_jobs WHERE job_id = ?",
            (job_id,),
        ).fetchone()
        is_new = exists is None
        result[job_id] = is_new
        if is_new:
            connection.execute(
                "INSERT INTO seen_jobs (job_id, first_seen) VALUES (?, ?)",
                (job_id, now),
            )
    connection.commit()
    return result
