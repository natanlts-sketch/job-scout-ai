from __future__ import annotations

import html
import re
from datetime import datetime, timedelta, timezone
from typing import Iterable


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    without_tags = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", html.unescape(without_tags)).strip()


def contains_term(text: str, terms: Iterable[str]) -> bool:
    normalized = text.lower()
    return any(term.lower() in normalized for term in terms if term)


def parse_date(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def job_is_recent(published_at: str, max_age_days: int) -> bool:
    published = parse_date(published_at)
    if published is None:
        return True
    now = datetime.now(timezone.utc)
    if published.tzinfo is None:
        published = published.replace(tzinfo=timezone.utc)
    else:
        published = published.astimezone(timezone.utc)
    return published >= now - timedelta(days=max_age_days)


def safe_filename(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_\u0590-\u05FF-]+", "_", value.strip())
    return cleaned.strip("_") or "file"
