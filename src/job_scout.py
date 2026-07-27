"""CLI entrypoint for Job Scout AI."""
from __future__ import annotations

from src.core.config import get_path, load_config
from src.core.logging_setup import setup_logging
from src.cv.generator import generate_tailored_cvs
from src.notify import send_email_report_from_html
from src.search import run_search


def main() -> None:
    setup_logging()
    load_config()
    result = run_search(trigger_type="cli")
    new_jobs = result["new_jobs"]
    cv_keywords = result["cv_keywords"]

    master = get_path("master_cv")
    tailored = []
    if master.exists() and new_jobs:
        tailored = generate_tailored_cvs(
            jobs=new_jobs,
            master_cv_path=master,
            output_directory=get_path("tailored_cvs"),
            cv_keywords=cv_keywords,
            also_pdf=True,
        )

    reports = result["reports"]
    send_email_report_from_html(reports["html"], len(new_jobs))

    print(f"Fetched: {result['fetched']}")
    print(f"Matched: {result['matched']}")
    print(f"New jobs: {result['new_count']}")
    if result["errors"]:
        print("Source errors:")
        for err in result["errors"]:
            print(f"  - {err}")
    print(f"Created {len(tailored)} tailored CVs.")
    print(f"CSV:  {reports['csv']}")
    print(f"XLSX: {reports['xlsx']}")
    print(f"HTML: {reports['html']}")


if __name__ == "__main__":
    main()
