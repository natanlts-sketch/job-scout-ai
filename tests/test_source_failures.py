from src.sources import fetch_all_jobs
from src.sources.remotive import RemotiveSource


def test_source_failure_isolated(monkeypatch):
    def boom(self):
        raise RuntimeError("source down")

    monkeypatch.setattr(RemotiveSource, "fetch", boom)

    # Only remotive enabled for this test via monkeypatch of get_enabled_sources
    import src.sources as sources

    monkeypatch.setattr(sources, "get_enabled_sources", lambda config=None: [RemotiveSource()])
    jobs, errors = fetch_all_jobs(source_names=["remotive"])
    assert jobs == []
    assert errors
    assert "remotive" in errors[0].lower() or "source down" in errors[0].lower()
