def calculate_match(cv_keywords, job_keywords):
    if not job_keywords:
        return 0.0, []

    cv_set = {k.lower() for k in cv_keywords}
    matches = [k for k in job_keywords if k.lower() in cv_set]
    score = round((len(matches) / len(job_keywords)) * 100, 2)
    return score, matches
