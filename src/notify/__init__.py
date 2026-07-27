from __future__ import annotations

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from src.core.db import initialize_database
from src.core.logging_setup import get_logger
from src.core.models import Job
from src.matching.scorer import bucket_jobs

logger = get_logger("jobscout.notify")


def email_enabled() -> bool:
    return os.getenv("EMAIL_ENABLED", "false").lower() == "true"


def _already_notified(user_id: int, job_id: str, kind: str) -> bool:
    with initialize_database() as conn:
        row = conn.execute(
            """
            SELECT 1 FROM notifications
            WHERE user_id = ? AND job_id = ? AND kind = ?
            """,
            (user_id, job_id, kind),
        ).fetchone()
    return row is not None


def _record_notification(user_id: int, job_id: str | None, kind: str, channel: str = "email") -> None:
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).isoformat()
    with initialize_database() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO notifications (user_id, job_id, channel, kind, sent_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, job_id, channel, kind, now),
        )
        conn.commit()


def send_html_email(subject: str, html_body: str, to_addr: str | None = None) -> None:
    required = ["SMTP_HOST", "SMTP_PORT", "EMAIL_FROM", "EMAIL_PASSWORD", "EMAIL_TO"]
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise RuntimeError(f"Missing email settings: {', '.join(missing)}")

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = os.environ["EMAIL_FROM"]
    message["To"] = to_addr or os.environ["EMAIL_TO"]
    message.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.environ["SMTP_PORT"])) as server:
        server.starttls()
        server.login(os.environ["EMAIL_FROM"], os.environ["EMAIL_PASSWORD"])
        server.send_message(message)
    logger.info("Sent email: %s", subject)


def send_test_email() -> str:
    if not email_enabled():
        return "EMAIL_ENABLED is false"
    send_html_email("Job Scout test email", "<p>Test email from Job Scout AI.</p>")
    return "Test email sent"


def build_daily_report_html(jobs: list[Job], dashboard_url: str = "http://localhost:8501") -> str:
    buckets = bucket_jobs(jobs)

    def section(title: str, items: list[Job]) -> str:
        if not items:
            return f"<h2>{title}</h2><p>None</p>"
        rows = []
        for job in items:
            rows.append(
                f"<li><a href='{job.url}'>{job.title}</a> — {job.company} "
                f"(ATS {job.ats_score}%, skills: {job.matched_skills})</li>"
            )
        return f"<h2>{title} ({len(items)})</h2><ul>{''.join(rows)}</ul>"

    return f"""
    <html><body>
    <h1>Daily Job Scout Report</h1>
    <p>New matching jobs: {len(jobs)}</p>
    <p><a href="{dashboard_url}">Open dashboard</a></p>
    {section("Israel / Local", buckets["israel_local"])}
    {section("Remote", buckets["remote"])}
    {section("Overseas", buckets["overseas"])}
    </body></html>
    """


def send_daily_report(user_id: int, jobs: list[Job], *, notifications_enabled: bool = True) -> int:
    if not email_enabled() or not notifications_enabled:
        return 0

    # Only jobs not yet reported
    fresh = [j for j in jobs if not _already_notified(user_id, j.job_id, "daily_report")]
    if not fresh:
        logger.info("No new jobs to email for user %s", user_id)
        return 0

    html = build_daily_report_html(fresh)
    send_html_email(f"Daily junior data jobs: {len(fresh)} new matches", html)
    for job in fresh:
        _record_notification(user_id, job.job_id, "daily_report")
    return len(fresh)


def send_high_match_alerts(
    user_id: int,
    jobs: list[Job],
    threshold: float,
    *,
    notifications_enabled: bool = True,
) -> int:
    if not email_enabled() or not notifications_enabled:
        return 0
    sent = 0
    for job in jobs:
        if job.ats_score < threshold:
            continue
        if _already_notified(user_id, job.job_id, "high_match"):
            continue
        send_html_email(
            f"High match: {job.title} at {job.company} ({job.ats_score}%)",
            f"<p>ATS {job.ats_score}% — <a href='{job.url}'>Open job</a></p>"
            f"<p>{job.match_explanation}</p>",
        )
        _record_notification(user_id, job.job_id, "high_match")
        sent += 1
    return sent


def send_email_report_from_html(html_path: Path, job_count: int) -> None:
    """CLI-compatible helper."""
    if not email_enabled():
        return
    send_html_email(
        f"Daily junior data jobs: {job_count} matches",
        html_path.read_text(encoding="utf-8"),
    )
