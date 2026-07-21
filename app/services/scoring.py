import re

TECH_GROUPS = {
    "Python": ["python"],
    "Django": ["django"],
    "FastAPI": ["fastapi"],
    "Flask": ["flask"],
    "AI/ML": ["artificial intelligence","machine learning","generative ai","genai","llm","langchain","pytorch","tensorflow","openai"],
    "Backend": ["backend","back-end","api development","microservices","rest api","graphql"],
    "Cloud": ["aws","azure","google cloud","gcp","docker","kubernetes","serverless"],
    "Data": ["data engineering","airflow","spark","pandas","etl","data pipeline"],
    "Automation": ["selenium","playwright","automation","web scraping"],
    "PostgreSQL": ["postgresql","postgres"],
    "Redis": ["redis","celery"],
}

HIRING_TERMS = [
    "we are hiring","join our team","open positions","open roles","careers",
    "vacancies","jobs","apply now","hiring","work with us"
]
CONTRACT_TERMS = [
    "staff augmentation","dedicated developers","development partner","outsourcing",
    "consulting","product engineering","custom software","managed team",
    "remote team","contract","nearshore","offshore"
]
QUALITY_TERMS = [
    "case studies","clients","portfolio","testimonials","awards","certified",
    "years of experience","global delivery","our work","trusted by"
]

def split_csv(value: str) -> list[str]:
    return [x.strip() for x in re.split(r"[,\n]", value or "") if x.strip()]

def detect_technologies(text: str) -> list[str]:
    lower = text.lower()
    return [name for name, terms in TECH_GROUPS.items() if any(term in lower for term in terms)]

def opportunity_score(text: str, careers_url: str, contact_url: str, emails: list[str], technologies: list[str], job_count: int):
    lower = text.lower()
    reasons = []
    technical = 0
    python_hits = [x for x in ["Python","Django","FastAPI","Flask"] if x in technologies]
    if python_hits:
        technical += min(22, 10 + len(python_hits) * 4)
        reasons.append("Python ecosystem detected: " + ", ".join(python_hits))
    if "AI/ML" in technologies:
        technical += 5
        reasons.append("AI/ML work detected")
    if "Backend" in technologies:
        technical += 3
    technical = min(30, technical)

    hiring_hits = sum(1 for term in HIRING_TERMS if term in lower)
    hiring = min(12, hiring_hits * 3)
    if careers_url:
        hiring += 5
        reasons.append("Careers page found")
    if job_count:
        hiring += min(8, job_count * 2)
        reasons.append(f"{job_count} relevant job signal(s) found")
    hiring = min(25, hiring)

    contract_hits = sum(1 for term in CONTRACT_TERMS if term in lower)
    contract = min(20, contract_hits * 4)
    if contract >= 8:
        reasons.append("Contract or agency delivery signals found")

    quality_hits = sum(1 for term in QUALITY_TERMS if term in lower)
    quality = min(15, quality_hits * 3)
    if quality >= 6:
        reasons.append("Credibility signals found")

    contact = 0
    if contact_url:
        contact += 4
        reasons.append("Contact page found")
    if emails:
        contact += 6
        reasons.append("Public business email found")
    contact = min(10, contact)

    total = min(100, technical + hiring + contract + quality + contact)
    if not reasons:
        reasons.append("Limited relevant public signals detected")
    return {
        "total": total, "technical": technical, "hiring": hiring,
        "contract": contract, "quality": quality, "contact": contact,
        "reasons": reasons,
    }

def profile_match(profile, technologies: list[str], text: str, jobs: list[dict]):
    profile_skills = split_csv(profile.skills)
    preferred_roles = split_csv(profile.preferred_roles)
    lower = text.lower()
    matched = []
    for skill in profile_skills:
        if skill.lower() in lower or any(skill.lower() in t.lower() or t.lower() in skill.lower() for t in technologies):
            matched.append(skill)
    skill_score = min(55, int((len(set(matched)) / max(1, len(profile_skills))) * 65))

    role_hits = 0
    job_titles = " ".join(j.get("title","") for j in jobs).lower()
    for role in preferred_roles:
        tokens = [x for x in re.split(r"\W+", role.lower()) if len(x) > 3]
        if tokens and sum(t in job_titles for t in tokens) >= max(1, len(tokens)//2):
            role_hits += 1
    role_score = min(30, role_hits * 10)

    remote_score = 0
    if profile.preferred_work_mode.lower() == "remote":
        if "remote" in lower or any(j.get("is_remote") for j in jobs):
            remote_score = 15

    total = min(100, skill_score + role_score + remote_score)
    reasons = []
    if matched:
        reasons.append("Matching skills: " + ", ".join(sorted(set(matched))[:10]))
    if role_hits:
        reasons.append(f"{role_hits} preferred role pattern(s) matched")
    if remote_score:
        reasons.append("Remote-work signal detected")
    if not reasons:
        reasons.append("No strong profile match detected yet")
    return total, reasons
