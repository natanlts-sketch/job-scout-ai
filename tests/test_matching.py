from src.core.models import Job
from src.core.text import job_is_recent, parse_date
from src.matching.scorer import add_ats_and_explanation, filter_jobs, score_job
from src.matching.skills import normalize_skill, normalize_skills
from src.matching.location import classify_job_geo


SAMPLE_CONFIG = {
    "search": {
        "keywords": ["data analyst", "junior data analyst", "bi analyst", "אנליסט נתונים"],
        "junior_terms": ["junior", "ג'וניור", "entry"],
        "excluded_terms": ["senior", "manager", "lead", "סניור"],
        "preferred_skills": ["sql", "python", "tableau", "power bi", "excel"],
        "high_weight_skills": ["sql", "python", "tableau", "power bi", "excel"],
        "locations": ["israel", "tel aviv", "remote", "ישראל", "תל אביב"],
        "israel_terms": ["israel", "ישראל", "tel aviv", "תל אביב"],
        "remote_terms": ["remote", "מרחוק"],
        "hybrid_terms": ["hybrid", "היברידי"],
        "onsite_terms": ["onsite", "on-site", "במשרד"],
        "minimum_score": 25,
        "max_age_days": 14,
    }
}


def _job(**kwargs):
    base = dict(
        source="Test",
        title="Junior Data Analyst",
        company="Acme",
        location="Tel Aviv, Israel",
        published_at="2026-07-20T10:00:00+00:00",
        url="https://example.com/job/1",
        description="Need SQL Python Tableau Excel Power BI",
    )
    base.update(kwargs)
    return Job(**base)


def test_score_junior_data_analyst_high():
    job = score_job(_job(), SAMPLE_CONFIG)
    assert job.score >= 25
    assert "sql" in job.matched_skills


def test_exclude_senior():
    job = score_job(_job(title="Senior Data Analyst Manager"), SAMPLE_CONFIG)
    assert job.score < score_job(_job(), SAMPLE_CONFIG).score


def test_hebrew_title_match():
    job = score_job(_job(title="אנליסט נתונים זוטר", location="תל אביב"), SAMPLE_CONFIG)
    assert job.score >= 25


def test_ats_matched_and_missing():
    job = score_job(_job(), SAMPLE_CONFIG)
    job = add_ats_and_explanation(job, ["sql", "python", "excel"], SAMPLE_CONFIG)
    assert job.ats_score > 0
    assert "sql" in job.matched_skills
    assert job.match_explanation
    assert "Missing" in job.match_explanation or job.missing_skills is not None


def test_normalize_hebrew_skills():
    assert normalize_skill("פייתון") == "python"
    assert normalize_skill("Power BI") == "power bi"
    assert "python" in normalize_skills(["פייתון", "python", "PYTHON"])


def test_region_israel_and_remote():
    local = classify_job_geo(_job(location="Tel Aviv, Israel"), SAMPLE_CONFIG)
    assert local.region == "israel_local"
    remote = classify_job_geo(
        _job(source="Remotive", location="Worldwide", description="Fully remote"),
        SAMPLE_CONFIG,
    )
    assert remote.work_type == "remote"
    assert remote.region in {"remote", "israel_local"}


def test_date_filter():
    assert job_is_recent("2026-07-20T00:00:00+00:00", 14) is True
    assert parse_date("not-a-date") is None


def test_minimum_score_filter():
    jobs = [score_job(_job(), SAMPLE_CONFIG), score_job(_job(title="CEO"), SAMPLE_CONFIG)]
    filtered = filter_jobs(jobs, SAMPLE_CONFIG, minimum_score=25)
    assert all(j.score >= 25 for j in filtered)
