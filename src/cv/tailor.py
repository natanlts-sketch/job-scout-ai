import re
from pathlib import Path

from docx import Document


def safe_filename(value: str) -> str:
    """Convert job/company text into a safe filename."""
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", value.strip())
    return cleaned.strip("_") or "tailored_cv"


def find_matching_keywords(
    cv_keywords: list[str],
    job_keywords: list[str],
    limit: int = 12,
) -> list[str]:
    """
    Return keywords that appear in both the master CV and job description.

    This prevents the tailored CV from claiming skills that are not already
    present in the original CV.
    """
    cv_set = {keyword.lower() for keyword in cv_keywords}

    matches = []
    for keyword in job_keywords:
        normalized = keyword.lower()

        if normalized in cv_set and normalized not in matches:
            matches.append(normalized)

    return matches[:limit]


def create_tailored_cv(
    master_cv_path: Path,
    output_directory: Path,
    job_title: str,
    company: str,
    matching_keywords: list[str],
) -> Path:
    """
    Create a job-specific copy of the master CV.

    The first version adds a truthful 'Relevant Skills' line using only
    keywords already present in the master CV.
    """
    document = Document(master_cv_path)

    if matching_keywords:
        skills_text = "Relevant Skills: " + ", ".join(
            keyword.title() for keyword in matching_keywords
        )

        paragraph = document.paragraphs[0].insert_paragraph_before(skills_text)
        paragraph.style = document.styles["Normal"]

    output_directory.mkdir(parents=True, exist_ok=True)

    filename = (
        f"{safe_filename(company)}_"
        f"{safe_filename(job_title)}_CV.docx"
    )

    output_path = output_directory / filename
    document.save(output_path)

    return output_path
