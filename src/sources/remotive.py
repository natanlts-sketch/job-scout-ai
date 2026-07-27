from __future__ import annotations

import requests

from src.core.models import Job
from src.core.text import clean_text
from src.core.logging_setup import get_logger

logger = get_logger("jobscout.sources.remotive")


class RemotiveSource:
    name = "remotive"
    endpoint = "https://remotive.com/api/remote-jobs"

    def fetch(self) -> list[Job]:
        response = requests.get(
            self.endpoint,
            timeout=30,
            headers={"User-Agent": "JuniorDataJobScout/2.0"},
        )
        response.raise_for_status()
        jobs: list[Job] = []
        for item in response.json().get("jobs", []):
            jobs.append(
                Job(
                    source="Remotive",
                    title=clean_text(item.get("title")),
                    company=clean_text(item.get("company_name")),
                    location=clean_text(item.get("candidate_required_location")),
                    published_at=clean_text(item.get("publication_date")),
                    url=clean_text(item.get("url")),
                    description=clean_text(item.get("description")),
                    external_id=str(item.get("id") or ""),
                )
            )
        logger.info("Remotive fetched %s jobs", len(jobs))
        return jobs
