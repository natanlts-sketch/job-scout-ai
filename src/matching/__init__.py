"""Job matching package."""

__all__ = [
    "score_job",
    "add_ats_and_explanation",
    "filter_jobs",
    "bucket_jobs",
    "classify_job_geo",
]


def __getattr__(name: str):
    if name in {
        "score_job",
        "add_ats_and_explanation",
        "filter_jobs",
        "bucket_jobs",
    }:
        from src.matching import scorer

        return getattr(scorer, name)
    if name == "classify_job_geo":
        from src.matching.location import classify_job_geo

        return classify_job_geo
    raise AttributeError(name)
