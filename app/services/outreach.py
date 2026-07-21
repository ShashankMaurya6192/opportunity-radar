def build_outreach(company, profile, contact_name: str = "", channel: str = "email"):
    greeting = f"Hi {contact_name}," if contact_name else "Hi,"
    tech = company.technologies or "backend and product engineering"
    reason = (company.score_reasons.splitlines()[0] if company.score_reasons else "your engineering work")
    skills = ", ".join([x.strip() for x in profile.skills.split(",")[:5]])
    if channel == "linkedin":
        return (
            f"{greeting}\n\n"
            f"I came across {company.name} while researching teams working in {tech}. "
            f"I noticed {reason.lower()}. I am a Python backend developer with {profile.years_experience}+ years "
            f"of experience across {skills}, and I am currently available for remote contract or full-time work. "
            f"I would be glad to connect if your team may need backend or automation support.\n\n"
            f"{profile.name}"
        )
    subject = f"Python backend support for {company.name}"
    body = (
        f"{greeting}\n\n"
        f"I was researching {company.name} and noticed your work around {tech}. "
        f"{reason}.\n\n"
        f"I have {profile.years_experience}+ years of experience in {skills}. "
        f"I have worked on backend systems, API integrations, automation, and AI-enabled products, "
        f"and I am currently {profile.availability.lower()} for {profile.preferred_work_mode.lower()} opportunities.\n\n"
        f"If you are expanding the engineering team or occasionally work with contract developers, "
        f"I would be happy to share relevant examples and discuss where I could help.\n\n"
        f"{profile.email_signature}"
    )
    return subject + "\n\n" + body
