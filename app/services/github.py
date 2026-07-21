from urllib.parse import urlparse
import httpx

async def analyze_github(github_url: str) -> dict:
    if not github_url:
        return {"languages": [], "repos": 0, "activity": 0, "evidence": ""}
    path = urlparse(github_url).path.strip("/").split("/")
    if not path:
        return {"languages": [], "repos": 0, "activity": 0, "evidence": ""}
    org = path[0]
    headers = {"Accept":"application/vnd.github+json","User-Agent":"OpportunityRadar/3.0"}
    try:
        async with httpx.AsyncClient(timeout=12, headers=headers) as client:
            response = await client.get(f"https://api.github.com/orgs/{org}/repos?per_page=50&sort=updated")
            if response.status_code == 404:
                response = await client.get(f"https://api.github.com/users/{org}/repos?per_page=50&sort=updated")
            if response.status_code >= 400:
                return {"languages": [], "repos": 0, "activity": 0, "evidence": f"GitHub API returned {response.status_code}"}
            repos = response.json()
            languages = sorted({r.get("language") for r in repos if r.get("language")})
            activity = sum(1 for r in repos if r.get("pushed_at"))
            names = ", ".join(r.get("name","") for r in repos[:8])
            return {
                "languages": languages,
                "repos": len(repos),
                "activity": activity,
                "evidence": f"GitHub {org}: {len(repos)} public repos. Languages: {', '.join(languages)}. Recent repos: {names}",
            }
    except Exception as exc:
        return {"languages": [], "repos": 0, "activity": 0, "evidence": f"GitHub check failed: {exc}"}
