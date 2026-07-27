from src.matching.export import bucket_jobs, jobs_to_frame, sort_jobs
from src.core.models import Job
from src.notify import build_daily_report_html


def _j(region, score=10, **kw):
    data = dict(
        source="T",
        title="t",
        company="c",
        location="l",
        published_at="2026-07-01",
        url="https://example.com",
        description="d",
        region=region,
        score=score,
        ats_score=50,
        matched_skills="sql",
        is_new=True,
    )
    data.update(kw)
    return Job(**data)


def test_bucket_and_export_columns():
    jobs = [_j("israel_local", 40), _j("remote", 30), _j("overseas", 20)]
    buckets = bucket_jobs(jobs)
    assert len(buckets["israel_local"]) == 1
    frame = jobs_to_frame(jobs)
    assert "matched_skills" in frame.columns
    assert "application_status" in frame.columns
    sorted_jobs = sort_jobs(jobs, by="score")
    assert sorted_jobs[0].score == 40


def test_email_html_sections():
    html = build_daily_report_html([_j("remote", title="Remote DA", company="Z")])
    assert "Remote" in html
    assert "Open dashboard" in html
