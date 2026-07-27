from __future__ import annotations

import os
from datetime import datetime, timezone

from src.core.config import env_bool, env_int, load_config
from src.core.db import initialize_database
from src.core.logging_setup import get_logger
from src.core.models import Job

logger = get_logger("jobscout.ai")


def ai_is_enabled() -> bool:
    config = load_config()
    default = bool((config.get("ai") or {}).get("enabled_default", False))
    return env_bool("AI_ENABLED", default) and bool(os.getenv("ANTHROPIC_API_KEY"))


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _tokens_used_today(user_id: int | None) -> int:
    with initialize_database() as conn:
        row = conn.execute(
            "SELECT tokens_used FROM ai_usage WHERE user_id IS ? AND day = ?",
            (user_id, _today()),
        ).fetchone()
    return int(row["tokens_used"]) if row else 0


def _add_tokens(user_id: int | None, tokens: int) -> None:
    with initialize_database() as conn:
        conn.execute(
            """
            INSERT INTO ai_usage (user_id, day, tokens_used) VALUES (?, ?, ?)
            ON CONFLICT(user_id, day) DO UPDATE SET
                tokens_used = tokens_used + excluded.tokens_used
            """,
            (user_id, _today(), tokens),
        )
        conn.commit()


def _budget_ok(user_id: int | None) -> bool:
    config = load_config()
    budget = env_int(
        "AI_DAILY_TOKEN_BUDGET",
        int((config.get("ai") or {}).get("daily_token_budget", 100000)),
    )
    return _tokens_used_today(user_id) < budget


def _get_cache(user_id: int, job_id: str, feature: str) -> str | None:
    with initialize_database() as conn:
        row = conn.execute(
            """
            SELECT response_text FROM ai_cache
            WHERE user_id = ? AND job_id = ? AND feature = ?
            """,
            (user_id, job_id, feature),
        ).fetchone()
    return row["response_text"] if row else None


def _set_cache(user_id: int, job_id: str, feature: str, text: str, tokens: int) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with initialize_database() as conn:
        conn.execute(
            """
            INSERT INTO ai_cache (user_id, job_id, feature, response_text, tokens_used, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, job_id, feature) DO UPDATE SET
                response_text = excluded.response_text,
                tokens_used = excluded.tokens_used,
                created_at = excluded.created_at
            """,
            (user_id, job_id, feature, text, tokens, now),
        )
        conn.commit()


def _complete(prompt: str, user_id: int | None = None, max_tokens: int | None = None) -> tuple[str, int]:
    if not ai_is_enabled():
        raise RuntimeError("AI is disabled or ANTHROPIC_API_KEY is missing")
    if not _budget_ok(user_id):
        raise RuntimeError("Daily AI token budget exceeded")

    import anthropic

    config = load_config()
    model = os.getenv("AI_MODEL") or (config.get("ai") or {}).get("model") or "claude-sonnet-4-20250514"
    max_tokens = max_tokens or int((config.get("ai") or {}).get("max_tokens_per_call", 2048))

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(block.text for block in message.content if hasattr(block, "text"))
    tokens = int(getattr(message.usage, "input_tokens", 0) or 0) + int(
        getattr(message.usage, "output_tokens", 0) or 0
    )
    _add_tokens(user_id, tokens)
    return text.strip(), tokens


def rule_based_cover_letter(job: Job, skills: list[str]) -> str:
    skill_line = ", ".join(skills[:8]) if skills else job.matched_skills
    return (
        f"Dear Hiring Team,\n\n"
        f"I am writing to apply for the {job.title} position at {job.company}. "
        f"My experience includes {skill_line}. "
        f"I would welcome the opportunity to contribute to your team.\n\n"
        f"Kind regards\n"
    )


def rule_based_interview_notes(job: Job) -> str:
    return (
        f"Role: {job.title} at {job.company}\n"
        f"Matched skills to emphasize: {job.matched_skills}\n"
        f"Gaps to prepare for: {job.missing_skills}\n"
        f"Work type / region: {job.work_type} / {job.region}\n"
        f"Source: {job.url}\n"
    )


def analyze_job(
    user_id: int,
    job: Job,
    *,
    cv_text: str | None = None,
    ai_consent: bool = False,
) -> dict[str, str]:
    """Return analysis fields; uses Anthropic when enabled + consented, else rules."""
    feature = "analyze_job"
    cached = _get_cache(user_id, job.job_id, feature)
    if cached:
        return {"analysis": cached, "source": "cache"}

    if ai_is_enabled() and ai_consent:
        cv_block = ""
        if cv_text and ai_consent:
            cv_block = f"\nCandidate CV excerpt (user consented):\n{cv_text[:3000]}\n"
        prompt = (
            "Analyze this job for a junior data candidate. "
            "Extract required and preferred skills, explain match, list missing skills. "
            "Do not invent candidate experience.\n\n"
            f"Title: {job.title}\nCompany: {job.company}\n"
            f"Description:\n{job.description[:5000]}\n"
            f"{cv_block}"
            f"Known matched: {job.matched_skills}\nKnown missing: {job.missing_skills}\n"
        )
        try:
            text, tokens = _complete(prompt, user_id=user_id)
            _set_cache(user_id, job.job_id, feature, text, tokens)
            return {"analysis": text, "source": "anthropic"}
        except Exception as exc:  # noqa: BLE001
            logger.warning("AI analyze failed, falling back: %s", exc)

    text = (
        f"{job.match_explanation}\n\n"
        f"Required/preferred signals from JD keywords: {job.matched_skills}, {job.missing_skills}"
    )
    return {"analysis": text, "source": "rules"}


def generate_cover_letter(user_id: int, job: Job, skills: list[str], ai_consent: bool = False) -> str:
    feature = "cover_letter"
    cached = _get_cache(user_id, job.job_id, feature)
    if cached:
        return cached
    if ai_is_enabled() and ai_consent:
        prompt = (
            "Write a short truthful cover letter for this role. "
            "Only mention these candidate skills (do not invent others): "
            f"{', '.join(skills)}\n\n"
            f"Job: {job.title} at {job.company}\nJD:\n{job.description[:3000]}"
        )
        try:
            text, tokens = _complete(prompt, user_id=user_id)
            _set_cache(user_id, job.job_id, feature, text, tokens)
            return text
        except Exception as exc:  # noqa: BLE001
            logger.warning("AI cover letter failed: %s", exc)
    return rule_based_cover_letter(job, skills)


def generate_recruiter_message(user_id: int, job: Job, ai_consent: bool = False) -> str:
    feature = "recruiter_message"
    cached = _get_cache(user_id, job.job_id, feature)
    if cached:
        return cached
    if ai_is_enabled() and ai_consent:
        prompt = (
            f"Write a 2-3 sentence recruiter outreach message for {job.title} at {job.company}. "
            "Professional, no invented claims."
        )
        try:
            text, tokens = _complete(prompt, user_id=user_id, max_tokens=300)
            _set_cache(user_id, job.job_id, feature, text, tokens)
            return text
        except Exception as exc:  # noqa: BLE001
            logger.warning("AI recruiter message failed: %s", exc)
    return f"Hi — I'm interested in the {job.title} role at {job.company}. May I share my CV?"


def generate_interview_prep(user_id: int, job: Job, ai_consent: bool = False) -> str:
    feature = "interview_prep"
    cached = _get_cache(user_id, job.job_id, feature)
    if cached:
        return cached
    if ai_is_enabled() and ai_consent:
        prompt = (
            "Create interview prep notes and likely questions for this junior data role. "
            f"Title: {job.title}\nCompany: {job.company}\n"
            f"Matched: {job.matched_skills}\nMissing: {job.missing_skills}\n"
            f"JD:\n{job.description[:4000]}"
        )
        try:
            text, tokens = _complete(prompt, user_id=user_id)
            _set_cache(user_id, job.job_id, feature, text, tokens)
            return text
        except Exception as exc:  # noqa: BLE001
            logger.warning("AI interview prep failed: %s", exc)
    return rule_based_interview_notes(job)
