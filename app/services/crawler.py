from __future__ import annotations
import asyncio, re
from datetime import datetime
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import httpx
from bs4 import BeautifulSoup
import tldextract
from .scoring import detect_technologies

USER_AGENT = "OpportunityRadar/3.0 (+local public research)"
PUBLIC_EMAIL_RE = re.compile(
    r"\b(?:hello|contact|careers|jobs|hiring|info|team|sales|support|business|partnerships|work)"
    r"@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I
)
PAGE_HINTS = (
    "about","services","technology","expertise","careers","jobs","contact",
    "work","portfolio","case-studies","blog","news","press","team"
)
JOB_HINTS = (
    "python","django","fastapi","backend","back-end","software engineer",
    "machine learning","ai engineer","data engineer","automation","selenium"
)

def normalize_url(value: str) -> str:
    value = value.strip()
    if not value.startswith(("http://","https://")):
        value = "https://" + value
    p = urlparse(value)
    return f"{p.scheme}://{p.netloc}"

def domain_from_url(url: str) -> str:
    ext = tldextract.extract(url)
    return ".".join(x for x in [ext.domain, ext.suffix] if x)

async def robots_allowed(client: httpx.AsyncClient, base: str, target: str) -> bool:
    try:
        response = await client.get(urljoin(base, "/robots.txt"), timeout=6)
        if response.status_code >= 400:
            return True
        rp = RobotFileParser()
        rp.parse(response.text.splitlines())
        return rp.can_fetch(USER_AGENT, target)
    except Exception:
        return True

def parse_page(html: str):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script","style","noscript","svg"]):
        tag.decompose()
    text = re.sub(r"\s+", " ", " ".join(soup.stripped_strings))
    return text, soup

def job_from_link(label: str, href: str, surrounding: str = ""):
    candidate = f"{label} {surrounding}".strip()
    lower = candidate.lower()
    if not any(x in lower for x in JOB_HINTS):
        return None
    location = ""
    for pattern in ["remote","london","new york","toronto","sydney","india","europe","uk","usa","canada","australia"]:
        if pattern in lower:
            location = pattern.title()
            break
    skills = [x for x in ["Python","Django","FastAPI","Flask","Backend","AI/ML","Data","Selenium","AWS","Docker"]
              if x.lower().replace("/ml","") in lower]
    return {
        "title": label[:300] or "Relevant engineering role",
        "url": href,
        "location": location,
        "skills": skills,
        "is_remote": "remote" in lower,
    }

async def crawl_company(url: str, max_pages: int = 12) -> dict:
    base = normalize_url(url)
    base_netloc = urlparse(base).netloc
    headers = {"User-Agent": USER_AGENT, "Accept":"text/html,application/xhtml+xml"}
    timeout = httpx.Timeout(15.0, connect=8.0)
    visited, queued = set(), {base}
    queue = [base]
    pages, evidence, jobs = [], [], []
    careers_url = contact_url = github_url = ""
    name = domain_from_url(base).split(".")[0].replace("-"," ").title()

    async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=timeout) as client:
        while queue and len(visited) < max_pages:
            page_url = queue.pop(0)
            if page_url in visited:
                continue
            if not await robots_allowed(client, base, page_url):
                continue
            visited.add(page_url)
            try:
                response = await client.get(page_url)
                if response.status_code >= 400 or "text/html" not in response.headers.get("content-type",""):
                    continue
            except Exception:
                continue
            text, soup = parse_page(response.text)
            pages.append(text)
            evidence.append(f"{page_url}\\n{text[:500]}")
            if len(visited) == 1 and soup.title and soup.title.string:
                title = re.split(r"[|–—]", soup.title.string)[0].strip()
                if title:
                    name = title[:250]

            for a in soup.find_all("a", href=True):
                href = urljoin(page_url, a["href"])
                label = a.get_text(" ", strip=True)
                parsed = urlparse(href)
                combined = f"{label} {parsed.path}".lower()

                if "github.com/" in href.lower() and not github_url:
                    github_url = href
                if parsed.netloc != base_netloc:
                    continue
                if any(x in combined for x in ("career","/jobs","vacanc","join-us")):
                    careers_url = careers_url or href
                if "contact" in combined:
                    contact_url = contact_url or href
                job = job_from_link(label, href, a.parent.get_text(" ", strip=True)[:250] if a.parent else "")
                if job and all(j["url"] != href for j in jobs):
                    jobs.append(job)
                if any(h in combined for h in PAGE_HINTS) and href not in visited and href not in queued:
                    queue.append(href)
                    queued.add(href)

    combined_text = "\n".join(pages)
    technologies = detect_technologies(combined_text)
    emails = sorted(set(PUBLIC_EMAIL_RE.findall(combined_text)))
    services = [s for s in [
        "Custom software","Consulting","Staff augmentation","Product engineering",
        "AI development","Cloud development","Data engineering"
    ] if s.lower() in combined_text.lower()]

    return {
        "name": name,
        "website": base,
        "domain": domain_from_url(base),
        "description": combined_text[:1200] if combined_text else "Website could not be read.",
        "full_text": combined_text,
        "technologies": technologies,
        "services": services,
        "github_url": github_url,
        "careers_url": careers_url,
        "contact_url": contact_url,
        "public_emails": emails,
        "evidence": evidence[:12],
        "jobs": jobs[:30],
        "checked_at": datetime.utcnow(),
    }

async def crawl_many(urls: list[str], concurrency: int = 5):
    sem = asyncio.Semaphore(max(1, concurrency))
    async def one(url):
        async with sem:
            try:
                return await crawl_company(url)
            except Exception as exc:
                return {"error": str(exc), "website": url}
    return await asyncio.gather(*(one(u) for u in urls))
