from __future__ import annotations

from src.core.config import load_config
from src.core.logging_setup import get_logger
from src.core.models import Job
from src.sources.arbeitnow import ArbeitnowSource
from src.sources.remoteok import RemoteOKSource
from src.sources.remotive import RemotiveSource

logger = get_logger("jobscout.sources")

SOURCE_REGISTRY = {
    "remotive": RemotiveSource,
    "remoteok": RemoteOKSource,
    "arbeitnow": ArbeitnowSource,
}


def get_enabled_sources(config: dict | None = None) -> list:
    config = config or load_config()
    enabled = (config.get("sources") or {}).get("enabled", ["remotive"])
    sources = []
    for name in enabled:
        cls = SOURCE_REGISTRY.get(name.lower())
        if cls:
            sources.append(cls())
        else:
            logger.warning("Unknown source skipped: %s", name)
    return sources


def dedupe_jobs(jobs: list[Job]) -> list[Job]:
    """Prevent the same job appearing from multiple sources (URL or title+company)."""
    seen_ids: set[str] = set()
    seen_keys: set[str] = set()
    unique: list[Job] = []
    for job in jobs:
        if not job.url and not job.title:
            continue
        key = f"{job.title.lower()}|{job.company.lower()}"
        if job.job_id in seen_ids or key in seen_keys:
            continue
        seen_ids.add(job.job_id)
        seen_keys.add(key)
        unique.append(job)
    return unique


def fetch_all_jobs(
    source_names: list[str] | None = None,
    config: dict | None = None,
) -> tuple[list[Job], list[str]]:
    """Fetch from all sources; collect errors without aborting the run."""
    config = config or load_config()
    if source_names:
        sources = []
        for name in source_names:
            cls = SOURCE_REGISTRY.get(name.lower())
            if cls:
                sources.append(cls())
    else:
        sources = get_enabled_sources(config)

    all_jobs: list[Job] = []
    errors: list[str] = []
    for source in sources:
        try:
            jobs = source.fetch()
            all_jobs.extend(jobs)
            logger.info("Source %s OK (%s jobs)", source.name, len(jobs))
        except Exception as exc:  # noqa: BLE001 — isolate source failures
            message = f"{source.name}: {exc}"
            errors.append(message)
            logger.error("Source unavailable — %s", message)
    return dedupe_jobs(all_jobs), errors
