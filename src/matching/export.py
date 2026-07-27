from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.core.models import EXPORT_COLUMNS, Job
from src.matching.scorer import bucket_jobs


def jobs_to_frame(jobs: list[Job]) -> pd.DataFrame:
    rows = []
    for job in jobs:
        data = job.to_dict()
        row = {col: data.get(col) for col in EXPORT_COLUMNS}
        row["is_new"] = "NEW" if data.get("is_new") else "Seen"
        rows.append(row)
    if not rows:
        return pd.DataFrame(columns=EXPORT_COLUMNS)
    frame = pd.DataFrame(rows)
    return frame.sort_values(["score", "ats_score", "published_at"], ascending=[False, False, False])


def export_reports(jobs: list[Job], report_dir: Path, stamp: str | None = None) -> dict[str, Path]:
    from datetime import datetime

    report_dir.mkdir(parents=True, exist_ok=True)
    stamp = stamp or datetime.now().strftime("%Y-%m-%d")
    frame = jobs_to_frame(jobs)

    csv_path = report_dir / f"jobs_{stamp}.csv"
    xlsx_path = report_dir / f"jobs_{stamp}.xlsx"
    html_path = report_dir / f"jobs_{stamp}.html"

    frame.to_csv(csv_path, index=False, encoding="utf-8-sig")

    buckets = bucket_jobs(jobs)
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        jobs_to_frame(jobs).to_excel(writer, sheet_name="All", index=False)
        jobs_to_frame(buckets["israel_local"]).to_excel(writer, sheet_name="Israel_Local", index=False)
        jobs_to_frame(buckets["remote"]).to_excel(writer, sheet_name="Remote", index=False)
        jobs_to_frame(buckets["overseas"]).to_excel(writer, sheet_name="Overseas", index=False)

    display = frame.copy()
    if not display.empty and "url" in display.columns:
        display["title"] = display.apply(
            lambda row: f'<a href="{row["url"]}">{row["title"]}</a>',
            axis=1,
        )
        display = display.drop(columns=["url"], errors="ignore")

    table = display.to_html(index=False, escape=False)
    html_path.write_text(
        f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Job Scout</title>
<style>
body{{font-family:system-ui,sans-serif;margin:24px}}
table{{border-collapse:collapse;width:100%;font-size:14px}}
th,td{{padding:8px;border:1px solid #ddd;text-align:left}}
th{{background:#f4f4f4}}
.badge{{background:#0a7;color:#fff;padding:2px 6px;border-radius:4px;font-size:12px}}
</style></head>
<body>
<h1>Job Scout AI</h1>
<p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")} · Matches: {len(frame)}</p>
{table}
</body></html>""",
        encoding="utf-8",
    )
    return {"csv": csv_path, "xlsx": xlsx_path, "html": html_path}


def filter_frame(
    jobs: list[Job],
    *,
    region: str | None = None,
    work_type: str | None = None,
    source: str | None = None,
    min_score: int | None = None,
    query: str | None = None,
) -> list[Job]:
    result = jobs
    if region:
        result = [j for j in result if j.region == region]
    if work_type:
        result = [j for j in result if j.work_type == work_type]
    if source:
        result = [j for j in result if j.source.lower() == source.lower()]
    if min_score is not None:
        result = [j for j in result if j.score >= min_score]
    if query:
        q = query.lower()
        result = [
            j
            for j in result
            if q in j.title.lower() or q in j.company.lower() or q in (j.location or "").lower()
        ]
    return result


def sort_jobs(jobs: list[Job], by: str = "score", descending: bool = True) -> list[Job]:
    key_map = {
        "score": lambda j: j.score,
        "ats_score": lambda j: j.ats_score,
        "date": lambda j: j.published_at or "",
        "company": lambda j: j.company.lower(),
        "title": lambda j: j.title.lower(),
    }
    key = key_map.get(by, key_map["score"])
    return sorted(jobs, key=key, reverse=descending)
