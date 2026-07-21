from __future__ import annotations
from dataclasses import asdict, dataclass
import re

STOP={"and","the","with","for","from","that","this","your","you","our","are","will","have","has","into","using","work","role","team","years","experience","developer","engineer"}
@dataclass(slots=True)
class MatchReport:
    score:int; matched_skills:list[str]; missing_skills:list[str]; role_alignment:int; experience_alignment:int; remote_alignment:int; explanation:str
    def as_dict(self): return asdict(self)

def normalize(v): return re.sub(r"\s+"," ",re.sub(r"[^a-z0-9+#./ -]+"," ",(v or "").lower())).strip()
def extract_keywords(text,limit=40):
    out=[]
    for x in re.findall(r"[a-zA-Z][a-zA-Z0-9+#./-]{1,}",normalize(text)):
        if x not in STOP and len(x)>2 and x not in out: out.append(x)
    return out[:limit]
def split_values(v):
    parts=re.split(r"[,;\n|]",v) if isinstance(v,str) else list(v); out=[]
    for p in parts:
        x=normalize(str(p))
        if x and x not in out: out.append(x)
    return out
def match_job(*,profile_skills,preferred_roles,years_experience,preferred_work_mode,resume_text,job_title,job_description="",job_skills=(),is_remote=False):
    candidate=set(split_values(profile_skills))|set(extract_keywords(resume_text,80))
    required=set(split_values(job_skills))|set(extract_keywords(job_description,35))
    matched=sorted(x for x in required if any(x in c or c in x for c in candidate)); missing=sorted(x for x in required if x not in matched)
    skill=50 if not required else round(100*len(matched)/max(1,len(required)))
    title=normalize(job_title); roles=split_values(preferred_roles)
    role=100 if any(r in title or title in r for r in roles) else 55 if set(extract_keywords(job_title,12))&candidate else 30
    m=re.search(r"(\d+)\s*\+?\s*(?:years|yrs)",normalize(job_description)); req=int(m.group(1)) if m else 0
    exp=100 if not req or years_experience>=req else max(20,round(years_experience/req*100))
    remote=100 if "remote" not in normalize(preferred_work_mode) or is_remote else 35
    score=round(skill*.55+role*.20+exp*.15+remote*.10)
    return MatchReport(score,matched[:20],missing[:20],role,exp,remote,f"{len(matched)} matched requirement(s), {len(missing)} gap(s). Role alignment {role}%, experience alignment {exp}%, work-mode alignment {remote}%.")
def match_company_jobs(profile,company):
    out=[]
    for job in getattr(company,"jobs",[]):
        if not getattr(job,"is_active",True): continue
        r=match_job(profile_skills=getattr(profile,"skills",""),preferred_roles=getattr(profile,"preferred_roles",""),years_experience=float(getattr(profile,"years_experience",0) or 0),
            preferred_work_mode=getattr(profile,"preferred_work_mode",""),resume_text=getattr(profile,"resume_text","") or "",job_title=getattr(job,"title",""),
            job_description=getattr(job,"description","") or "",job_skills=getattr(job,"skills",""),is_remote=bool(getattr(job,"is_remote",False)))
        out.append((job,r))
    return sorted(out,key=lambda x:x[1].score,reverse=True)
