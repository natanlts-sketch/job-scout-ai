from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Job:
    source: str
    title: str
    company: str
    location: str
    published_at: str
    url: str
    description: str
    score: int = 0
    ats_score: float = 0.0
    matched_skills: str = ""
    missing_skills: str = ""
    match_explanation: str = ""
    work_type: str = ""  # remote | hybrid | onsite | unknown
    region: str = ""  # israel_local | remote | overseas
    is_new: bool = True
    application_status: str = "New"
    external_id: str = ""

    @property
    def job_id(self) -> str:
        raw = f"{self.source}|{self.title}|{self.company}|{self.url}".lower()
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["job_id"] = self.job_id
        return data


APPLICATION_STATUSES = [
    "New",
    "Reviewed",
    "Saved",
    "Rejected",
    "Preparing",
    "Applied",
    "Interview",
    "Technical interview",
    "Offer",
    "Closed",
]


EXPORT_COLUMNS = [
    "title",
    "company",
    "location",
    "work_type",
    "region",
    "published_at",
    "source",
    "score",
    "ats_score",
    "matched_skills",
    "missing_skills",
    "match_explanation",
    "url",
    "application_status",
    "is_new",
]
