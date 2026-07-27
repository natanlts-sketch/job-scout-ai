from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from datetime import datetime, timezone
from typing import Any

from src.core.db import initialize_database
from src.core.logging_setup import get_logger

logger = get_logger("jobscout.auth")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def hash_password(password: str) -> str:
    """PBKDF2-SHA256 password hash (stdlib — Streamlit Cloud friendly)."""
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        200_000,
    ).hex()
    return f"pbkdf2${salt}${digest}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        if password_hash.startswith("pbkdf2$"):
            _, salt, digest = password_hash.split("$", 2)
            check = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt.encode("utf-8"),
                200_000,
            ).hex()
            return hmac.compare_digest(check, digest)

        # Legacy bcrypt hashes (local installs that still have bcrypt)
        import bcrypt  # type: ignore

        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


def create_user(email: str, password: str, display_name: str = "") -> dict[str, Any]:
    email = email.strip().lower()
    if not email or not password or len(password) < 8:
        raise ValueError("Valid email and password (min 8 chars) required")

    now = utc_now()
    with initialize_database() as conn:
        existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            raise ValueError("Email already registered")
        cur = conn.execute(
            """
            INSERT INTO users (email, password_hash, display_name, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (email, hash_password(password), display_name or email.split("@")[0], now, now),
        )
        user_id = cur.lastrowid
        conn.execute(
            """
            INSERT INTO user_preferences (user_id, updated_at)
            VALUES (?, ?)
            """,
            (user_id, now),
        )
        conn.commit()
        logger.info("Created user %s", email)
        return get_user_by_id(user_id)


def authenticate(email: str, password: str) -> dict[str, Any] | None:
    email = email.strip().lower()
    with initialize_database() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ? AND is_active = 1",
            (email,),
        ).fetchone()
    if not row:
        return None
    if not verify_password(password, row["password_hash"]):
        return None
    return dict(row)


def get_user_by_id(user_id: int) -> dict[str, Any] | None:
    with initialize_database() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def delete_user_and_data(user_id: int) -> None:
    with initialize_database() as conn:
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
    logger.info("Deleted user %s and cascaded data", user_id)


def get_preferences(user_id: int) -> dict[str, Any]:
    with initialize_database() as conn:
        row = conn.execute(
            "SELECT * FROM user_preferences WHERE user_id = ?",
            (user_id,),
        ).fetchone()
    if not row:
        return {}
    data = dict(row)
    for key in (
        "preferred_titles",
        "preferred_locations",
        "preferred_languages",
        "excluded_companies",
        "excluded_keywords",
        "preferred_sources",
    ):
        try:
            data[key] = json.loads(data.get(key) or "[]")
        except json.JSONDecodeError:
            data[key] = []
    return data


def save_preferences(user_id: int, prefs: dict[str, Any]) -> None:
    now = utc_now()

    def dumps(value: Any) -> str:
        if isinstance(value, str):
            return value
        return json.dumps(value or [])

    with initialize_database() as conn:
        conn.execute(
            """
            INSERT INTO user_preferences (
                user_id, preferred_titles, preferred_locations, remote_preference,
                minimum_ats_score, experience_level, preferred_languages,
                excluded_companies, excluded_keywords, preferred_sources,
                salary_preference, email_notifications, ai_consent,
                search_frequency_hours, language, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                preferred_titles=excluded.preferred_titles,
                preferred_locations=excluded.preferred_locations,
                remote_preference=excluded.remote_preference,
                minimum_ats_score=excluded.minimum_ats_score,
                experience_level=excluded.experience_level,
                preferred_languages=excluded.preferred_languages,
                excluded_companies=excluded.excluded_companies,
                excluded_keywords=excluded.excluded_keywords,
                preferred_sources=excluded.preferred_sources,
                salary_preference=excluded.salary_preference,
                email_notifications=excluded.email_notifications,
                ai_consent=excluded.ai_consent,
                search_frequency_hours=excluded.search_frequency_hours,
                language=excluded.language,
                updated_at=excluded.updated_at
            """,
            (
                user_id,
                dumps(prefs.get("preferred_titles", [])),
                dumps(prefs.get("preferred_locations", [])),
                prefs.get("remote_preference", "any"),
                float(prefs.get("minimum_ats_score") or 0),
                prefs.get("experience_level", "junior"),
                dumps(prefs.get("preferred_languages", ["en", "he"])),
                dumps(prefs.get("excluded_companies", [])),
                dumps(prefs.get("excluded_keywords", [])),
                dumps(prefs.get("preferred_sources", [])),
                prefs.get("salary_preference"),
                1 if prefs.get("email_notifications", True) else 0,
                1 if prefs.get("ai_consent", False) else 0,
                int(prefs.get("search_frequency_hours") or 24),
                prefs.get("language", "he"),
                now,
            ),
        )
        conn.commit()


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def create_login_session(user_id: int, days: int | None = None) -> str:
    """Create a durable login session token (default from config, min 1 day)."""
    from datetime import timedelta

    from src.core.config import load_config

    config = load_config()
    configured = int((config.get("security") or {}).get("session_days", 1))
    days = max(1, int(days if days is not None else configured))
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=days)
    token = new_session_token()
    with initialize_database() as conn:
        conn.execute(
            """
            INSERT INTO user_sessions (token, user_id, expires_at, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (token, user_id, expires.isoformat(), now.isoformat()),
        )
        conn.commit()
    return token


def get_user_by_session_token(token: str | None) -> dict[str, Any] | None:
    if not token:
        return None
    now = datetime.now(timezone.utc).isoformat()
    with initialize_database() as conn:
        row = conn.execute(
            """
            SELECT u.*
            FROM user_sessions s
            JOIN users u ON u.id = s.user_id
            WHERE s.token = ? AND s.expires_at >= ? AND u.is_active = 1
            """,
            (token, now),
        ).fetchone()
        if not row:
            conn.execute("DELETE FROM user_sessions WHERE token = ?", (token,))
            conn.commit()
            return None
        return dict(row)


def revoke_session_token(token: str | None) -> None:
    if not token:
        return
    with initialize_database() as conn:
        conn.execute("DELETE FROM user_sessions WHERE token = ?", (token,))
        conn.commit()


def revoke_user_sessions(user_id: int) -> None:
    with initialize_database() as conn:
        conn.execute("DELETE FROM user_sessions WHERE user_id = ?", (user_id,))
        conn.commit()
