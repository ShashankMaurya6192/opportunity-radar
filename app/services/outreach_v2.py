from __future__ import annotations
from dataclasses import dataclass
from .intelligence import report_from_company
from .matching import match_company_jobs
@dataclass(slots=True)
class OutreachDraft:
    channel:str; subject:str; body:str; evidence_used:list[str]; warnings:list[str]
def build_personalized_outreach(company,profile,channel="email",contact_name=""):
    intel=report_from_company(company); reports=match_company_jobs(profile,company); best,rept=reports[0] if reports else (None,None)
    evidence=[]; warnings=[]
    if getattr(company,"technologies",""): evidence.append(f"Stack: {company.technologies}")
    if best:evidence.append(f"Role: {best.title} ({rept.score}% match)")
    if getattr(company,"careers_url",""):evidence.append("Active careers page")
    if not evidence:warnings.append("Limited company-specific evidence; review carefully before sending.")
    greeting=f"Hi {(contact_name or 'there').split()[0]},"
    name=getattr(company,"name","your company"); pname=getattr(profile,"name",""); headline=getattr(profile,"headline","Python backend developer")
    skills=", ".join([x.strip() for x in (getattr(profile,"skills","") or "").split(",")[:4] if x.strip()])
    tech=", ".join([x.strip() for x in (getattr(company,"technologies","") or "").split(",")[:4] if x.strip()])
    if best:
        relevance=f"I noticed the {best.title} opportunity and compared it with my background. The strongest overlap is in {', '.join(rept.matched_skills[:5]) or skills}."
        ask=f"Would you be open to a brief conversation about the {best.title} role?"; subject=f"{best.title} — {pname}"
    else:
        relevance=f"I came across {name} while researching {intel.company_type.lower()} teams"+(f" using {tech}" if tech else "")+"."
        ask="Would a short conversation about current or upcoming backend needs be useful?"; subject=f"Python backend support for {name}"
    proof=f"I’m a {headline} with {getattr(profile,'years_experience','')}+ years of experience in {skills}. I am {getattr(profile,'availability','available').lower()}."
    if channel=="linkedin":
        body=f"{greeting}\n\n{relevance} {proof} {ask}"; return OutreachDraft("linkedin","",body[:700],evidence,warnings)
    sig=getattr(profile,"email_signature","") or f"Best regards,\n{pname}"
    return OutreachDraft("email",subject,f"{greeting}\n\n{relevance}\n\n{proof}\n\n{intel.recommended_angle}\n\n{ask}\n\n{sig}",evidence,warnings)
