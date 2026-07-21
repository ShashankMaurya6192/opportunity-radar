from app.services.discovery import DiscoveryCandidate, build_queries, deduplicate_candidates, is_company_candidate


def test_build_queries_are_unique_and_include_location():
    queries = build_queries("Python backend", "United Kingdom", True)
    assert len(queries) == 3
    assert all("United Kingdom" in query for query in queries)
    assert all("remote" in query.lower() for query in queries)


def test_social_and_job_boards_are_rejected():
    assert not is_company_candidate("https://www.linkedin.com/company/example")
    assert not is_company_candidate("https://indeed.com/jobs?q=python")
    assert is_company_candidate("https://example.com/careers")


def test_candidates_are_deduplicated_by_domain():
    candidates = [
        DiscoveryCandidate("https://example.com", "example.com"),
        DiscoveryCandidate("https://www.example.com/careers", "example.com"),
        DiscoveryCandidate("https://another.dev", "another.dev"),
    ]
    assert len(deduplicate_candidates(candidates)) == 2
