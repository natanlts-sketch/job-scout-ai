from src.cv.parser import CVParser
from src.cv.keywords import extract_keywords
from src.cv.scorer import calculate_match

# Load your CV
cv = CVParser("data/cv/master_cv.docx")
cv_text = cv.get_text()

# Extract CV keywords
cv_keywords = extract_keywords(cv_text)

# Example job description
job_description = """
Junior Data Analyst
Requirements:
SQL
Python
Tableau
Power BI
Data Cleaning
ETL
Excel
"""

# Extract job keywords
job_keywords = extract_keywords(job_description)

# Calculate score
score, matches = calculate_match(cv_keywords, job_keywords)

print("=" * 40)
print("ATS MATCH SCORE:", score, "%")
print("=" * 40)
print("Matched keywords:")
print(matches)
print("=" * 40)
