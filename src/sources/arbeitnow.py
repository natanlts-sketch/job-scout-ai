from __future__ import annotations

import requests

from src.core.models import Job
from src.core.text import clean_text
from src.core.logging_setup import get_logger

logger = get_logger("jobscout.sources.arbeitnow")


class ArbeitnowSource:
    """Arbeitnow public job board API."""

    name = "arbeitnow"
    endpoint = "https://www.arbeitnow.com/api/job-board-api"

    def fetch(self) -> list[Job]:
        response = requests.get(
            self.endpoint,
            timeout=30,
            headers={"User-Agent": "JuniorDataJobScout/2.0"},
        )
        response.raise_for_status()
        jobs: list[Job] = []
        for item in response.json().get("data", []):
            tags = item.get("tags") or []
            types = item.get("job_types") or []
            extra = " ".join(str(t) for t in list(tags) + list(types))
            jobs.append(
                Job(
                    source="Arbeitnow",
                    title=clean_text(item.get("title")),
                    company=clean_text(item.get("company_name")),
                    location=clean_text(item.get("location")),
                    published_at=clean_text(str(item.get("created_at") or "")),
                    url=clean_text(item.get("url")),
                    description=clean_text((item.get("description") or "") + " " + extra),
                    external_id=clean_text(item.get("slug") or ""),
                )
            )
        logger.info("Arbeitnow fetched %s jobs", len(jobs))
        return jobs
