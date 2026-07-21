from __future__ import annotations
from dataclasses import asdict, dataclass
import json, re

@dataclass(slots=True)
class Signal:
    key: str
    label: str
    score: int
    evidence: str

@dataclass(slots=True)
class IntelligenceReport:
    company_type: str
    estimated_size: str
    hiring_probability: int
    engineering_maturity: int
    outreach_probability: int
    risk_level: str
    summary: str
    recommended_angle: str
    signals: list[Signal]
    def as_dict(self):
        d=asdict(self); d["signals"]=[asdict(x) for x in self.signals]; return d
    def as_json(self): return json.dumps(self.as_dict(), ensure_ascii=False)

HIRING={"careers":20,"we are hiring":25,"join our team":20,"open positions":20,"vacancies":16,"job openings":20,"growing team":12}
ENGINEERING={"github":12,"engineering blog":14,"open source":12,"api":8,"cloud":7,"docker":8,"kubernetes":10,"ci/cd":9,"microservices":9,"machine learning":8}
AGENCY=("agency","consulting","consultancy","client services","staff augmentation")
PRODUCT=("saas","platform","product company","subscription","our product")
STARTUP=("startup","seed funded","series a","series b","venture backed")
RISK=("unpaid","commission only","crypto opportunity","guaranteed income")

def _hits(text, terms):
    low=text.lower(); return [x for x in terms if x in low]

def _size(text):
    patterns=[(r"\b(?:1|2|3|4|5|6|7|8|9|10)[-– ]?(?:person|people|employee|member)","1–10"),
              (r"\b(?:11|12|15|20|25|30|40|50)[-– ]?(?:person|people|employee|member)","11–50"),
              (r"\b(?:51|60|75|100|150|200)[-– ]?(?:person|people|employee|member)","51–200"),
              (r"\b(?:201|250|300|500)[-– ]?(?:person|people|employee|member)","201–500"),
              (r"\b(?:501|750|1000|\d{4,})[-– ]?(?:person|people|employee|member)","500+")]
    for p,b in patterns:
        m=re.search(p,text,re.I)
        if m:return b,m.group(0)
    return ("500+","Enterprise/global-office language") if ("enterprise" in text.lower() or "global offices" in text.lower()) else ("Unknown","No reliable employee-count evidence")

def analyze_company(*, text, technologies=(), services=(), jobs=(), careers_url="", contact_url="", github_url="", public_emails=()):
    text=text or ""; technologies=[str(x).strip() for x in technologies if str(x).strip()]; services=[str(x).strip() for x in services if str(x).strip()]; jobs=list(jobs); public_emails=list(public_emails)
    groups=[("Software agency / consultancy",_hits(" ".join([text,*services]),AGENCY)),("Product / SaaS company",_hits(text,PRODUCT)),("Startup",_hits(text,STARTUP))]
    company_type,hits=max(groups,key=lambda x:len(x[1]))
    if not hits: company_type,hits="Technology company",["General technology signals"]
    size,size_ev=_size(text)
    hiring=24 if careers_url else 0; he=["Dedicated careers page"] if careers_url else []
    if jobs: hiring+=min(42,14+len(jobs)*7); he.append(f"{len(jobs)} relevant role(s) detected")
    for term,weight in HIRING.items():
        if term in text.lower(): hiring+=weight; he.append(term)
    hiring=min(100,hiring)
    engineering=min(42,len(set(technologies))*5); ee=[f"{len(set(technologies))} technologies detected"] if technologies else []
    if github_url: engineering+=18; ee.append("Public GitHub presence")
    for term,weight in ENGINEERING.items():
        if term in text.lower(): engineering+=weight; ee.append(term)
    engineering=min(100,engineering)
    contact=0; ce=[]
    if contact_url: contact+=25; ce.append("Contact page")
    if public_emails: contact+=min(35,20+len(public_emails)*5); ce.append(f"{len(public_emails)} public business email(s)")
    if github_url: contact+=10
    if company_type.startswith("Software agency"): contact+=12; ce.append("Client-services company")
    contact=min(100,contact)
    risk_hits=_hits(text,RISK); risk="High" if len(risk_hits)>=2 else "Medium" if risk_hits else "Low"
    outreach=round(hiring*.45+engineering*.35+contact*.20)-(25 if risk=="High" else 0); outreach=max(0,outreach)
    signals=[Signal("company_type","Company type",0,", ".join(hits[:3])),Signal("company_size","Estimated size",0,size_ev),
             Signal("hiring","Hiring intent",hiring,"; ".join(he[:6]) or "No strong hiring evidence"),
             Signal("engineering","Engineering maturity",engineering,"; ".join(ee[:6]) or "Limited technical evidence"),
             Signal("contactability","Contactability",contact,"; ".join(ce[:5]) or "No direct public route found"),
             Signal("risk","Risk",100 if risk=="High" else 50 if risk=="Medium" else 10,", ".join(risk_hits) or "No obvious risk phrases")]
    top=", ".join(technologies[:5]) or "an unspecified technology stack"
    summary=f"{company_type} with an estimated size of {size}. The site shows a {hiring}% hiring-intent score and {engineering}% engineering-maturity score. Detected stack: {top}. Outreach probability is {outreach}% based only on public evidence."
    if jobs: angle=f"Lead with direct fit for {', '.join(str(j.get('title','role')) for j in jobs[:3])}; reference the detected stack and immediate availability."
    elif company_type.startswith("Software agency"): angle="Offer flexible backend capacity for client delivery, emphasizing Python, APIs, automation and fast onboarding."
    else: angle="Use a concise engineering-value message tied to the detected stack; ask about upcoming backend hiring."
    return IntelligenceReport(company_type,size,hiring,engineering,outreach,risk,summary,angle,signals)

def report_from_company(company):
    jobs=[{"title":j.title,"skills":j.skills,"location":j.location,"is_remote":j.is_remote} for j in getattr(company,"jobs",[]) if getattr(j,"is_active",True)]
    return analyze_company(text=" ".join([getattr(company,"description","") or "",getattr(company,"evidence","") or "",getattr(company,"score_reasons","") or ""]),
        technologies=(getattr(company,"technologies","") or "").split(","),services=(getattr(company,"services","") or "").split(","),jobs=jobs,
        careers_url=getattr(company,"careers_url","") or "",contact_url=getattr(company,"contact_url","") or "",github_url=getattr(company,"github_url","") or "",
        public_emails=(getattr(company,"public_emails","") or "").split(","))
