from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone

from src.core.db import initialize_database


def _rows(sql: str, params: tuple = ()) -> list[dict]:
    with initialize_database() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def jobs_found_per_day(days: int = 30) -> list[dict]:
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    return _rows(
        """
        SELECT substr(first_seen, 1, 10) AS day, COUNT(*) AS count
        FROM jobs WHERE first_seen >= ?
        GROUP BY day ORDER BY day
        """,
        (since,),
    )


def new_jobs_per_week(user_id: int | None = None) -> list[dict]:
    if user_id:
        return _rows(
            """
            SELECT substr(created_at, 1, 10) AS day, SUM(is_new) AS new_count
            FROM job_matches WHERE user_id = ?
            GROUP BY day ORDER BY day
            """,
            (user_id,),
        )
    return _rows(
        """
        SELECT substr(first_seen, 1, 10) AS day, COUNT(*) AS new_count
        FROM seen_jobs GROUP BY day ORDER BY day
        """
    )


def jobs_by_field(field: str) -> list[dict]:
    if field not in {"region", "source", "work_type"}:
        raise ValueError("Invalid field")
    return _rows(f"SELECT {field} AS label, COUNT(*) AS count FROM jobs GROUP BY {field}")


def average_ats(user_id: int) -> float:
    rows = _rows(
        "SELECT AVG(ats_score) AS avg_ats FROM job_matches WHERE user_id = ?",
        (user_id,),
    )
    return float(rows[0]["avg_ats"] or 0) if rows else 0.0


def skill_frequency(user_id: int, column: str = "matched_skills", limit: int = 15) -> list[dict]:
    if column not in {"matched_skills", "missing_skills"}:
        raise ValueError("Invalid column")
    rows = _rows(f"SELECT {column} AS skills FROM job_matches WHERE user_id = ?", (user_id,))
    counter: Counter[str] = Counter()
    for row in rows:
        raw = row.get("skills") or ""
        for part in raw.split(","):
            skill = part.strip().lower()
            if skill:
                counter[skill] += 1
    return [{"skill": s, "count": c} for s, c in counter.most_common(limit)]


def application_funnel(user_id: int) -> list[dict]:
    return _rows(
        """
        SELECT status, COUNT(*) AS count
        FROM applications WHERE user_id = ?
        GROUP BY status
        """,
        (user_id,),
    )


def application_rates(user_id: int) -> dict:
    rows = _rows(
        "SELECT status, COUNT(*) AS count FROM applications WHERE user_id = ? GROUP BY status",
        (user_id,),
    )
    counts = {r["status"]: r["count"] for r in rows}
    applied = counts.get("Applied", 0) + counts.get("Interview", 0) + counts.get(
        "Technical interview", 0
    ) + counts.get("Offer", 0) + counts.get("Closed", 0)
    interviews = (
        counts.get("Interview", 0)
        + counts.get("Technical interview", 0)
        + counts.get("Offer", 0)
    )
    offers = counts.get("Offer", 0)
    return {
        "applied": applied,
        "interviews": interviews,
        "offers": offers,
        "response_rate": round((interviews / applied) * 100, 1) if applied else 0.0,
        "success_rate": round((offers / applied) * 100, 1) if applied else 0.0,
        "companies_applied": _rows(
            """
            SELECT COUNT(DISTINCT j.company) AS c
            FROM applications a JOIN jobs j ON j.job_id = a.job_id
            WHERE a.user_id = ? AND a.status IN (
                'Applied','Interview','Technical interview','Offer','Closed'
            )
            """,
            (user_id,),
        )[0]["c"]
        if True
        else 0,
    }


def dashboard_stats(user_id: int) -> dict:
    with initialize_database() as conn:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        found_today = conn.execute(
            """
            SELECT COUNT(*) AS c FROM job_matches
            WHERE user_id = ? AND substr(created_at,1,10) = ?
            """,
            (user_id, today),
        ).fetchone()["c"]
        new_matches = conn.execute(
            "SELECT COUNT(*) AS c FROM job_matches WHERE user_id = ? AND is_new = 1",
            (user_id,),
        ).fetchone()["c"]
        best = conn.execute(
            """
            SELECT j.title, j.company, m.ats_score, j.url
            FROM job_matches m JOIN jobs j ON j.job_id = m.job_id
            WHERE m.user_id = ?
            ORDER BY m.ats_score DESC, m.score DESC LIMIT 1
            """,
            (user_id,),
        ).fetchone()
        applied = conn.execute(
            "SELECT COUNT(*) AS c FROM applications WHERE user_id = ? AND status = 'Applied'",
            (user_id,),
        ).fetchone()["c"]
        saved = conn.execute(
            "SELECT COUNT(*) AS c FROM applications WHERE user_id = ? AND status = 'Saved'",
            (user_id,),
        ).fetchone()["c"]
    return {
        "found_today": found_today,
        "new_matches": new_matches,
        "best_match": dict(best) if best else None,
        "applications_sent": applied,
        "saved_jobs": saved,
        "avg_ats": average_ats(user_id),
        "funnel": application_funnel(user_id),
        "rates": application_rates(user_id),
        "by_region": jobs_by_field("region"),
        "by_source": jobs_by_field("source"),
        "top_matched_skills": skill_frequency(user_id, "matched_skills"),
        "top_missing_skills": skill_frequency(user_id, "missing_skills"),
        "jobs_per_day": jobs_found_per_day(),
    }
