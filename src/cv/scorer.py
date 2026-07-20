def calculate_match(cv_keywords, job_keywords):
    if not job_keywords:
        return 0

    matches = [k for k in job_keywords if k in cv_keywords]

    score = round((len(matches) / len(job_keywords)) * 100, 2)

    return score, matches
