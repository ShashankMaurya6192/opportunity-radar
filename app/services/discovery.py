from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from urllib.parse import urlparse

from ddgs import DDGS

from ..config import settings
from .crawler import crawl_many, domain_from_url

logger = logging.getLogger(__name__)

BLOCKED_HOSTS = {
    "linkedin.com", "facebook.com", "instagram.com", "x.com", "twitter.com",
    "youtube.com", "crunchbase.com", "glassdoor.com", "indeed.com",
}


@dataclass(slots=True)
class DiscoveryCandidate:
    url: str
    domain: str
    title: str = ""
    snippet: str = ""
    source_query: str = ""


@dataclass(slots=True)
class DiscoveryBatch:
    queries: list[str]
    candidates: list[DiscoveryCandidate] = field(default_factory=list)
    crawled: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def build_queries(query: str, country: str = "", remote_only: bool = False) -> list[str]:
    query = " ".join(query.split())
    country = " ".join(country.split())
    location = f" {country}" if country else ""
    remote = " remote" if remote_only else ""
    variants = [
        f"{query}{location}{remote}",
        f'"{query}" company{location}{remote}',
        f'"{query}" careers{location}{remote}',
    ]
    return list(dict.fromkeys(v.strip() for v in variants if v.strip()))


def is_company_candidate(url: str) -> bool:
    try:
        parsed = urlparse(url)
        host = parsed.netloc.lower().removeprefix("www.")
        if parsed.scheme not in {"http", "https"} or not host:
            return False
        if any(host == blocked or host.endswith(f".{blocked}") for blocked in BLOCKED_HOSTS):
            return False
        return bool(domain_from_url(url))
    except Exception:
        return False


def deduplicate_candidates(items: list[DiscoveryCandidate]) -> list[DiscoveryCandidate]:
    by_domain: dict[str, DiscoveryCandidate] = {}
    for item in items:
        by_domain.setdefault(item.domain.lower(), item)
    return list(by_domain.values())


def search_candidates(query: str, max_results: int) -> list[DiscoveryCandidate]:
    results = DDGS().text(query, max_results=max_results)
    candidates: list[DiscoveryCandidate] = []
    for item in results:
        url = item.get("href") or item.get("url") or ""
        if not is_company_candidate(url):
            continue
        candidates.append(
            DiscoveryCandidate(
                url=url,
                domain=domain_from_url(url),
                title=item.get("title", ""),
                snippet=item.get("body", "") or item.get("snippet", ""),
                source_query=query,
            )
        )
    return candidates


async def discover_companies(
    query: str,
    country: str = "",
    limit: int = 10,
    remote_only: bool = False,
    concurrency: int | None = None,
) -> DiscoveryBatch:
    capped_limit = max(1, min(limit, settings.discovery_max_results))
    queries = build_queries(query, country, remote_only)
    batch = DiscoveryBatch(queries=queries)

    per_query = max(5, min(capped_limit, 20))
    for generated_query in queries:
        try:
            batch.candidates.extend(await asyncio.to_thread(search_candidates, generated_query, per_query))
        except Exception as exc:
            logger.warning("Search failed for %r: %s", generated_query, exc)
            batch.errors.append(f"{generated_query}: {exc}")

    batch.candidates = deduplicate_candidates(batch.candidates)[:capped_limit]
    if not batch.candidates:
        return batch

    batch.crawled = await crawl_many(
        [candidate.url for candidate in batch.candidates],
        concurrency=concurrency or settings.discovery_concurrency,
    )
    return batch
