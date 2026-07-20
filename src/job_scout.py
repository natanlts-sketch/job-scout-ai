from __future__ import annotations

import hashlib
import html
import os
import re
import smtplib
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Iterable

import pandas as pd
import requests
import yaml
from dotenv import load_dotenv

from src.cv.parser import CVParser
from src.cv.keywords import extract_keywords
from src.cv.scorer import calculate_match
from src.cv.generator import generate_tailored_cvs

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "jobs.db"
REPORT_DIR = BASE_DIR / "reports"
CONFIG_PATH = BASE_DIR / "config.yaml"
MASTER_CV_PATH = BASE_DIR / "data" / "cv" / "master_cv.docx"


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
    matched_skills: str = ""
    ats_score: float = 0.0
    is_new: bool = True

    @property
    def job_id(self) -> str:
        raw = f"{self.source}|{self.title}|{self.company}|{self.url}".lower()
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    without_tags = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", html.unescape(without_tags)).strip()


def fetch_remotive_jobs() -> list[Job]:
    """Fetch active jobs from Remotive's public API."""
    endpoint = "https://remotive.com/api/remote-jobs"
    response = requests.get(
        endpoint,
        timeout=30,
        headers={"User-Agent": "JuniorDataJobScout/1.0"},
    )
    response.raise_for_status()

    jobs = []
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
            )
        )
    return jobs


def contains_term(text: str, terms: Iterable[str]) -> bool:
    normalized = text.lower()
    return any(term.lower() in normalized for term in terms)


def parse_date(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def score_job(job: Job, config: dict) -> Job:
    search = config["search"]
    title = job.title.lower()
    full_text = f"{job.title} {job.description} {job.location}".lower()

    score = 0

    if contains_term(title, search["keywords"]):
        score += 35

    if contains_term(title, search["junior_terms"]):
        score += 25

    if contains_term(title, search["excluded_terms"]):
        score -= 45

    matched_skills = [
        skill for skill in search["preferred_skills"]
        if skill.lower() in full_text
    ]
    score += min(len(matched_skills) * 7, 28)

    if contains_term(job.location, search["locations"]):
        score += 12

    job.score = max(score, 0)
    job.matched_skills = ", ".join(matched_skills)
    return job


def add_ats_score(job: Job, cv_keywords: list[str]) -> Job:
    job_text = f"{job.title} {job.description}"
    job_keywords = extract_keywords(job_text)

    score, _ = calculate_match(cv_keywords, job_keywords)
    job.ats_score = score

    return job


def job_is_recent(job: Job, max_age_days: int) -> bool:
    published = parse_date(job.published_at)
    if published is None:
        return True
    now = datetime.now(timezone.utc)
    if published.tzinfo is None:
        published = published.replace(tzinfo=timezone.utc)
    else:
        published = published.astimezone(timezone.utc)

    return published >= now - timedelta(days=max_age_days)


def initialize_database() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS seen_jobs (
            job_id TEXT PRIMARY KEY,
            first_seen TEXT NOT NULL
        )
        """
    )
    connection.commit()
    return connection


def mark_new_jobs(jobs: list[Job], connection: sqlite3.Connection) -> list[Job]:
    now = datetime.now(timezone.utc).isoformat()

    for job in jobs:
        exists = connection.execute(
            "SELECT 1 FROM seen_jobs WHERE job_id = ?",
            (job.job_id,),
        ).fetchone()

        job.is_new = exists is None

        if job.is_new:
            connection.execute(
                "INSERT INTO seen_jobs (job_id, first_seen) VALUES (?, ?)",
                (job.job_id, now),
            )

    connection.commit()
    return jobs


def create_reports(jobs: list[Job]) -> tuple[Path, Path]:
    REPORT_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d")

    columns = [
        "score","ats_score", "title", "company", "location", "published_at",
        "matched_skills", "source", "url", "is_new"
    ]
    frame = pd.DataFrame([asdict(job) for job in jobs])
    if frame.empty:
        frame = pd.DataFrame(columns=columns)
    else:
        frame = frame[columns].sort_values(
            ["score", "published_at"], ascending=[False, False]
        )

    csv_path = REPORT_DIR / f"jobs_{stamp}.csv"
    html_path = REPORT_DIR / f"jobs_{stamp}.html"

    frame.to_csv(csv_path, index=False, encoding="utf-8-sig")

    display_frame = frame.copy()
    if not display_frame.empty:
        display_frame["title"] = display_frame.apply(
            lambda row: f'<a href="{html.escape(row["url"])}">{html.escape(row["title"])}</a>',
            axis=1,
        )
        display_frame["is_new"] = display_frame["is_new"].map(
            {True: "NEW", False: "Seen before"}
        )

    table = display_frame.drop(columns=["url"], errors="ignore").to_html(
        index=False, escape=False
    )
    page = f"""
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <title>Junior Data Job Scout</title>
      <style>
        body {{ font-family: Arial, sans-serif; margin: 32px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ padding: 10px; border: 1px solid #ddd; text-align: left; }}
        th {{ background: #f2f2f2; }}
        tr:nth-child(even) {{ background: #fafafa; }}
      </style>
    </head>
    <body>
      <h1>Junior Data Job Scout</h1>
      <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
      <p>Matching jobs: {len(frame)}</p>
      {table}
    </body>
    </html>
    """
    html_path.write_text(page, encoding="utf-8")
    return csv_path, html_path


def send_email_report(html_path: Path, job_count: int) -> None:
    if os.getenv("EMAIL_ENABLED", "false").lower() != "true":
        return

    required = ["SMTP_HOST", "SMTP_PORT", "EMAIL_FROM", "EMAIL_PASSWORD", "EMAIL_TO"]
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise RuntimeError(f"Missing email settings: {', '.join(missing)}")

    message = MIMEMultipart("alternative")
    message["Subject"] = f"Daily junior data jobs: {job_count} matches"
    message["From"] = os.environ["EMAIL_FROM"]
    message["To"] = os.environ["EMAIL_TO"]
    message.attach(MIMEText(html_path.read_text(encoding="utf-8"), "html"))

    with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.environ["SMTP_PORT"])) as server:
        server.starttls()
        server.login(os.environ["EMAIL_FROM"], os.environ["EMAIL_PASSWORD"])
        server.send_message(message)


def main() -> None:
    load_dotenv(BASE_DIR / ".env")
    config = load_config()
    search = config["search"]

    cv = CVParser(MASTER_CV_PATH)
    cv_text = cv.get_text()
    cv_keywords = extract_keywords(cv_text)

    print(f"CV loaded successfully: {len(cv_keywords)} keywords found.")


    print("Fetching jobs...")
    jobs = fetch_remotive_jobs()
    print(f"Fetched {len(jobs)} jobs.")

    jobs = [score_job(job, config) for job in jobs]
    jobs = [add_ats_score(job, cv_keywords) for job in jobs]
    jobs = [
        job for job in jobs
        if job.score >= search["minimum_score"]
        and job_is_recent(job, search["max_age_days"])
    ]

    with initialize_database() as connection:
        jobs = mark_new_jobs(jobs, connection)

    # Daily email contains only newly discovered listings.
    new_jobs = [job for job in jobs if job.is_new]

    tailored_cv_paths = []

    tailored_cv_paths = generate_tailored_cvs(
        jobs=new_jobs,
        master_cv_path=MASTER_CV_PATH,
        output_directory=BASE_DIR / "outputs" / "tailored_cvs",
        cv_keywords=cv_keywords,
    )

    csv_path, html_path = create_reports(new_jobs)
    send_email_report(html_path, len(new_jobs))

    print(f"Found {len(new_jobs)} new matching jobs.")
    print(f"Created {len(tailored_cv_paths)} tailored CVs.")
    print(f"CSV report:  {csv_path}")
    print(f"HTML report: {html_path}")

if __name__ == "__main__":
    main()
