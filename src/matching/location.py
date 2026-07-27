from __future__ import annotations

from src.core.models import Job
from src.core.text import contains_term


def detect_work_type(job: Job, config: dict) -> str:
    search = config.get("search", {})
    text = f"{job.title} {job.location} {job.description}".lower()

    if contains_term(text, search.get("hybrid_terms", [])):
        return "hybrid"
    if contains_term(text, search.get("remote_terms", [])):
        return "remote"
    if contains_term(text, search.get("onsite_terms", [])):
        return "onsite"
    # Remotive / remote-only sources default to remote
    if job.source.lower() in {"remotive", "remoteok"}:
        return "remote"
    return "unknown"


def detect_region(job: Job, work_type: str, config: dict) -> str:
    search = config.get("search", {})
    location = (job.location or "").lower()
    text = f"{job.location} {job.description}".lower()

    if work_type == "remote" and not contains_term(location, search.get("israel_terms", [])):
        # Worldwide remote
        if contains_term(text, search.get("israel_terms", [])):
            return "israel_local"
        return "remote"

    if contains_term(location, search.get("israel_terms", [])) or contains_term(
        text, search.get("israel_terms", [])
    ):
        return "israel_local"

    if work_type == "remote":
        return "remote"

    return "overseas"


def classify_job_geo(job: Job, config: dict) -> Job:
    work_type = detect_work_type(job, config)
    region = detect_region(job, work_type, config)
    job.work_type = work_type
    job.region = region
    return job
