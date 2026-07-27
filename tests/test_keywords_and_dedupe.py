from src.core.models import Job
from src.cv.keywords import extract_keywords
from src.cv.scorer import calculate_match
from src.sources import dedupe_jobs


def test_extract_keywords_english_and_phrases():
    text = "Experience with Power BI, Python, SQL and data visualization"
    keys = extract_keywords(text)
    assert "power bi" in keys
    assert "python" in keys
    assert "sql" in keys


def test_extract_keywords_hebrew():
    text = "ניסיון עם פייתון ואקסל וטבלו"
    keys = extract_keywords(text)
    assert "python" in keys
    assert "excel" in keys
    assert "tableau" in keys


def test_calculate_match():
    score, matches = calculate_match(["sql", "python"], ["sql", "tableau", "python"])
    assert score == round((2 / 3) * 100, 2)
    assert set(matches) == {"sql", "python"}


def test_calculate_match_empty_job():
    score, matches = calculate_match(["sql"], [])
    assert score == 0.0
    assert matches == []


def test_dedupe_jobs_across_sources():
    a = Job(
        source="Remotive",
        title="Data Analyst",
        company="X",
        location="Remote",
        published_at="",
        url="https://example.com/a",
        description="sql",
    )
    b = Job(
        source="RemoteOK",
        title="Data Analyst",
        company="X",
        location="Remote",
        published_at="",
        url="https://example.com/b",
        description="sql",
    )
    unique = dedupe_jobs([a, b])
    assert len(unique) == 1
