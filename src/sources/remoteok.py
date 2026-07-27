from __future__ import annotations

from datetime import datetime, timezone

import requests

from src.core.models import Job
from src.core.text import clean_text
from src.core.logging_setup import get_logger

logger = get_logger("jobscout.sources.remoteok")


class RemoteOKSource:
    """Public RemoteOK API — legal public JSON feed."""

    name = "remoteok"
    endpoint = "https://remoteok.com/api"

    def fetch(self) -> list[Job]:
        response = requests.get(
            self.endpoint,
            timeout=30,
            headers={"User-Agent": "JuniorDataJobScout/2.0"},
        )
        response.raise_for_status()
        payload = response.json()
        jobs: list[Job] = []
        for item in payload:
            if not isinstance(item, dict) or "id" not in item:
                continue
            epoch = item.get("epoch") or item.get("date")
            published = ""
            if isinstance(epoch, (int, float)):
                published = datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()
            elif isinstance(epoch, str):
                published = epoch

            tags = item.get("tags") or []
            tag_text = " ".join(str(t) for t in tags)
            description = clean_text(item.get("description") or tag_text)

            jobs.append(
                Job(
                    source="RemoteOK",
                    title=clean_text(item.get("position") or item.get("title")),
                    company=clean_text(item.get("company")),
                    location=clean_text(item.get("location") or "Remote"),
                    published_at=published,
                    url=clean_text(item.get("url") or item.get("apply_url")),
                    description=description,
                    external_id=str(item.get("id")),
                )
            )
        logger.info("RemoteOK fetched %s jobs", len(jobs))
        return jobs
