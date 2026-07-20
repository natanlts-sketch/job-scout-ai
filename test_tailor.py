from pathlib import Path

from src.cv.keywords import extract_keywords
from src.cv.parser import CVParser
from src.cv.tailor import create_tailored_cv, find_matching_keywords


master_cv = Path("data/cv/master_cv.docx")
output_dir = Path("outputs/tailored_cvs")

job_title = "Junior Data Analyst"
company = "Test Company"

job_description = """
We are looking for a Junior Data Analyst with experience in SQL, Python,
Tableau, webhooks, automation and Generative AI.
"""

cv_text = CVParser(master_cv).get_text()
cv_keywords = extract_keywords(cv_text)
job_keywords = extract_keywords(job_description)

matches = find_matching_keywords(cv_keywords, job_keywords)

output_path = create_tailored_cv(
    master_cv_path=master_cv,
    output_directory=output_dir,
    job_title=job_title,
    company=company,
    matching_keywords=matches,
)

print("Matching keywords:", matches)
print("Created:", output_path)
