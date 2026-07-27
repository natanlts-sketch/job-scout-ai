from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler

from src.auth import get_preferences
from src.core.db import initialize_database
from src.core.logging_setup import get_logger
from src.search import run_search

logger = get_logger("jobscout.scheduler")

_scheduler: BackgroundScheduler | None = None


def _active_user_ids() -> list[int]:
    with initialize_database() as conn:
        rows = conn.execute("SELECT id FROM users WHERE is_active = 1").fetchall()
    return [r["id"] for r in rows]


def scheduled_search_job() -> None:
    for user_id in _active_user_ids():
        prefs = get_preferences(user_id)
        try:
            logger.info("Scheduled search for user %s", user_id)
            run_search(user_id=user_id, trigger_type="scheduled")
        except Exception as exc:  # noqa: BLE001
            logger.error("Scheduled search failed for user %s: %s", user_id, exc)


def start_scheduler(default_hours: int = 24) -> BackgroundScheduler:
    global _scheduler
    if _scheduler and _scheduler.running:
        return _scheduler
    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        scheduled_search_job,
        "interval",
        hours=default_hours,
        id="daily_scout",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("Scheduler started (every %s hours)", default_hours)
    return _scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
