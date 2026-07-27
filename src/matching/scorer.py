from __future__ import annotations

from src.core.config import load_config
from src.core.models import Job
from src.core.text import contains_term, job_is_recent
from src.cv.keywords import extract_keywords
from src.cv.scorer import calculate_match
from src.matching.location import classify_job_geo
from src.matching.skills import HIGH_WEIGHT_SKILLS, normalize_skill, normalize_skills


def score_job(job: Job, config: dict | None = None) -> Job:
    config = config or load_config()
    search = config["search"]
    title = job.title.lower()
    full_text = f"{job.title} {job.description} {job.location}".lower()

    score = 0
    reasons: list[str] = []

    if contains_term(title, search["keywords"]):
        score += 35
        reasons.append("title matches target role")

    if contains_term(title, search["junior_terms"]):
        score += 25
        reasons.append("junior/entry-level signal in title")

    if contains_term(title, search["excluded_terms"]):
        score -= 45
        reasons.append("senior/manager exclusion in title")

    preferred = [normalize_skill(s) for s in search.get("preferred_skills", []) if s and not str(s).startswith("#")]
    high_weight = set(
        normalize_skill(s)
        for s in search.get("high_weight_skills", list(HIGH_WEIGHT_SKILLS))
        if s and not str(s).startswith("#")
    )

    matched_skills: list[str] = []
    for skill in preferred:
        if skill and skill in full_text:
            matched_skills.append(skill)
            if skill in high_weight:
                score += 10
            else:
                score += 7

    score = min(score, score)  # no-op clarity
    # Cap skill contribution roughly
    # already added per skill; soft cap via max later

    if contains_term(job.location, search["locations"]):
        score += 12
        reasons.append("preferred location match")

    job = classify_job_geo(job, config)
    if job.region == "israel_local":
        score += 5
        reasons.append("Israel/local role")
    elif job.region == "remote":
        score += 3
        reasons.append("remote role")

    job.score = max(score, 0)
    job.matched_skills = ", ".join(normalize_skills(matched_skills))
    return job


def add_ats_and_explanation(job: Job, cv_keywords: list[str], config: dict | None = None) -> Job:
    config = config or load_config()
    job_text = f"{job.title} {job.description}"
    job_keywords = extract_keywords(job_text)
    cv_norm = normalize_skills(cv_keywords)
    job_norm = normalize_skills(job_keywords)

    # Weighted ATS: high-weight skills count double in numerator/denominator
    high = set(
        normalize_skill(s)
        for s in (config.get("search") or {}).get("high_weight_skills", list(HIGH_WEIGHT_SKILLS))
        if s and not str(s).startswith("#")
    )

    if not job_norm:
        job.ats_score = 0.0
        job.missing_skills = ""
        job.match_explanation = "No extractable skills in job description."
        return job

    weighted_total = 0.0
    weighted_match = 0.0
    matches: list[str] = []
    missing: list[str] = []

    cv_set = set(cv_norm)
    for skill in job_norm:
        weight = 2.0 if skill in high else 1.0
        weighted_total += weight
        if skill in cv_set:
            weighted_match += weight
            matches.append(skill)
        else:
            missing.append(skill)

    score = round((weighted_match / weighted_total) * 100, 2) if weighted_total else 0.0
    # Also keep classic overlap for stability
    classic, classic_matches = calculate_match(cv_norm, job_norm)
    job.ats_score = round(max(score, classic * 0.85), 2)

    matched = normalize_skills(matches or classic_matches)
    missing = normalize_skills(missing)
    # Prefer showing preferred/high skills in missing list first
    preferred = [
        normalize_skill(s)
        for s in (config.get("search") or {}).get("preferred_skills", [])
        if s and not str(s).startswith("#")
    ]
    preferred_missing = [s for s in preferred if s in missing]
    other_missing = [s for s in missing if s not in preferred_missing]
    display_missing = (preferred_missing + other_missing)[:12]

    job.matched_skills = ", ".join(matched[:15])
    job.missing_skills = ", ".join(display_missing)

    parts = []
    if matched:
        parts.append(f"Matched: {', '.join(matched[:8])}")
    if display_missing:
        parts.append(f"Missing: {', '.join(display_missing[:6])}")
    if job.score:
        parts.append(f"Relevance score {job.score}")
    parts.append(f"ATS {job.ats_score}%")
    if job.work_type:
        parts.append(f"Work type: {job.work_type}")
    if job.region:
        parts.append(f"Region: {job.region}")
    job.match_explanation = " | ".join(parts)
    return job


def filter_jobs(
    jobs: list[Job],
    config: dict | None = None,
    minimum_score: int | None = None,
    minimum_ats: float | None = None,
    excluded_companies: list[str] | None = None,
    excluded_keywords: list[str] | None = None,
) -> list[Job]:
    config = config or load_config()
    search = config["search"]
    min_score = minimum_score if minimum_score is not None else search["minimum_score"]
    max_age = search["max_age_days"]
    excluded_companies = [c.lower() for c in (excluded_companies or [])]
    excluded_keywords = [k.lower() for k in (excluded_keywords or [])]

    filtered: list[Job] = []
    for job in jobs:
        if job.score < min_score:
            continue
        if not job_is_recent(job.published_at, max_age):
            continue
        if minimum_ats is not None and job.ats_score < minimum_ats:
            continue
        if job.company.lower() in excluded_companies:
            continue
        blob = f"{job.title} {job.description}".lower()
        if any(k in blob for k in excluded_keywords if k):
            continue
        filtered.append(job)
    return filtered


def bucket_jobs(jobs: list[Job]) -> dict[str, list[Job]]:
    buckets = {"israel_local": [], "remote": [], "overseas": []}
    for job in jobs:
        key = job.region if job.region in buckets else "overseas"
        buckets[key].append(job)
    return buckets
