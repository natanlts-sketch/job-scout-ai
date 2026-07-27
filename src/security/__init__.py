from __future__ import annotations

import hashlib
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from src.core.config import get_path
from src.core.logging_setup import get_logger

logger = get_logger("jobscout.security")


def _fernet():
    """Optional Fernet; falls back to None if cryptography is unavailable."""
    key = os.getenv("SETTINGS_ENCRYPTION_KEY", "").strip()
    if not key:
        return None
    try:
        from cryptography.fernet import Fernet

        return Fernet(key.encode("utf-8"))
    except Exception:
        return None


def encrypt_secret(value: str) -> str:
    fernet = _fernet()
    if not fernet:
        return f"plain:{value}"
    return fernet.encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_secret(value: str) -> str:
    if value.startswith("plain:"):
        return value[len("plain:") :]
    fernet = _fernet()
    if not fernet:
        return value
    try:
        from cryptography.fernet import InvalidToken

        return fernet.decrypt(value.encode("utf-8")).decode("utf-8")
    except Exception:
        return value


def backup_database() -> Path:
    db_path = get_path("database")
    backup_dir = get_path("backups")
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    target = backup_dir / f"jobs_{stamp}.db"
    if db_path.exists():
        shutil.copy2(db_path, target)
        logger.info("Database backed up to %s", target)
    return target


def user_upload_root(user_id: int) -> Path:
    root = get_path("uploads") / str(user_id)
    root.mkdir(parents=True, exist_ok=True)
    return root.resolve()


def assert_path_in_user_root(user_id: int, path: Path) -> Path:
    root = user_upload_root(user_id)
    resolved = path.resolve()
    if root not in resolved.parents and resolved != root:
        apps = (get_path("applications") / str(user_id)).resolve()
        if apps not in resolved.parents and resolved != apps:
            raise PermissionError("Path outside user sandbox")
    return resolved


def fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


PRIVACY_NOTICE = """
Job Scout AI Privacy Notice

- We store your account email, hashed password, CV files, preferences, and job activity locally (or on your deployed server).
- Passwords are hashed (PBKDF2) and never stored in plain text.
- API keys should live in environment variables, not in the UI.
- CV text is sent to Anthropic only if you enable AI and grant consent.
- You may delete your account and associated data at any time from Settings.
- Retention: search logs and notifications may be purged after 180 days (configurable in future releases).
- Backups: local SQLite backups are written to data/backups/.
"""
