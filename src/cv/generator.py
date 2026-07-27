from pathlib import Path

from src.cv.keywords import extract_keywords
from src.cv.tailor import create_tailored_cv, export_pdf_from_docx, find_matching_keywords


def generate_tailored_cvs(
    jobs,
    master_cv_path: Path,
    output_directory: Path,
    cv_keywords: list[str],
    *,
    also_pdf: bool = False,
) -> list[Path]:
    tailored_cv_paths = []

    for job in jobs:
        job_text = f"{job.title} {job.description}"
        job_keywords = extract_keywords(job_text)
        matching_keywords = find_matching_keywords(cv_keywords, job_keywords)
        tailored_cv_path = create_tailored_cv(
            master_cv_path=master_cv_path,
            output_directory=output_directory,
            job_title=job.title,
            company=job.company,
            matching_keywords=matching_keywords,
        )
        tailored_cv_paths.append(tailored_cv_path)
        if also_pdf:
            export_pdf_from_docx(tailored_cv_path)

    return tailored_cv_paths
