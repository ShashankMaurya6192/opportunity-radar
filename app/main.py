from __future__ import annotations
import asyncio, csv, io, json, logging
from datetime import datetime, timedelta
from urllib.parse import urlparse

from ddgs import DDGS
from fastapi import FastAPI, Request, Form, UploadFile, File, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func, or_, desc, asc
from sqlalchemy.orm import Session

from .config import settings
from .database import Base, engine, SessionLocal
from .exceptions import register_exception_handlers
from .logging_config import configure_logging
from .models import *
from .services.crawler import crawl_company, crawl_many, domain_from_url
from .services.github import analyze_github
from .services.scoring import opportunity_score, profile_match
from .services.outreach import build_outreach
from .services.scheduler import scheduler
from .services.discovery import discover_companies

configure_logging()
logger = logging.getLogger(__name__)
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name, version=settings.app_version, debug=settings.debug)
register_exception_handlers(app)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

STATUSES = ["NEW","HIGH_PRIORITY","REVIEW_LATER","CONTACTED","REPLIED","INTERVIEW","OFFER","NO_RESPONSE","REJECTED","NOT_RELEVANT","DO_NOT_CONTACT"]
PIPELINE_STATUSES = ["NEW","HIGH_PRIORITY","CONTACTED","REPLIED","INTERVIEW","OFFER"]

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

def get_profile(db: Session):
    p = db.get(UserProfile, 1)
    if not p:
        p = UserProfile(id=1)
        db.add(p); db.commit(); db.refresh(p)
    return p

def save_result(db: Session, result: dict, source_query: str = ""):
    profile = get_profile(db)
    company = db.scalar(select(Company).where(Company.domain == result["domain"]))
    old_score = company.combined_score if company else None
    old_jobs = {j.url for j in company.jobs} if company else set()

    if not company:
        company = Company(
            name=result["name"], domain=result["domain"], website=result["website"],
            first_discovered_at=datetime.utcnow(), source_query=source_query,
        )
        db.add(company); db.flush()

    opp = opportunity_score(
        result["full_text"], result["careers_url"], result["contact_url"],
        result["public_emails"], result["technologies"], len(result["jobs"])
    )
    match, match_reasons = profile_match(profile, result["technologies"], result["full_text"], result["jobs"])
    combined = round(opp["total"] * 0.55 + match * 0.45)
    previous_combined = company.combined_score or 0

    company.name = result["name"] or company.name
    company.website = result["website"]
    company.description = result["description"]
    company.technologies = ", ".join(result["technologies"])
    company.services = ", ".join(result["services"])
    company.github_url = result["github_url"]
    company.careers_url = result["careers_url"]
    company.contact_url = result["contact_url"]
    company.public_emails = ", ".join(result["public_emails"])
    company.evidence = "\n\n".join(result["evidence"])
    company.opportunity_score = opp["total"]
    company.match_score = match
    company.combined_score = combined
    company.score_delta = combined - previous_combined if old_score is not None else 0
    company.technical_score = opp["technical"]
    company.hiring_score = opp["hiring"]
    company.contract_score = opp["contract"]
    company.quality_score = opp["quality"]
    company.contact_score = opp["contact"]
    company.score_reasons = "\n".join(opp["reasons"])
    company.match_reasons = "\n".join(match_reasons)
    company.last_checked_at = result["checked_at"]
    if combined >= 80 and company.status == "NEW":
        company.status = "HIGH_PRIORITY"

    seen_urls = set()
    for jdata in result["jobs"]:
        seen_urls.add(jdata["url"])
        job = db.scalar(select(Job).where(Job.company_id==company.id, Job.url==jdata["url"]))
        if not job:
            job = Job(company_id=company.id, title=jdata["title"], url=jdata["url"])
            db.add(job)
            db.add(ChangeEvent(company_id=company.id, event_type="NEW_JOB", title=f"New job detected: {jdata['title']}", details=jdata["url"], importance=3))
        job.title = jdata["title"]
        job.location = jdata["location"]
        job.skills = ", ".join(jdata["skills"])
        job.is_remote = jdata["is_remote"]
        job.is_active = True
        job.last_seen_at = datetime.utcnow()
        # simple job match
        profile_skills = [x.strip().lower() for x in profile.skills.split(",")]
        job.match_score = min(100, sum(15 for s in profile_skills if s and s in (jdata["title"]+" "+job.skills).lower()))

    for old in company.jobs:
        if old.url not in seen_urls and old.last_seen_at and old.last_seen_at < datetime.utcnow() - timedelta(hours=1):
            old.is_active = False

    if old_score is not None and company.score_delta:
        direction = "increased" if company.score_delta > 0 else "decreased"
        db.add(ChangeEvent(
            company_id=company.id, event_type="SCORE_CHANGE",
            title=f"Combined score {direction} by {abs(company.score_delta)}",
            details=f"From {old_score} to {combined}", importance=2 if abs(company.score_delta)>=10 else 1
        ))

    db.add(ScoreHistory(
        company_id=company.id, opportunity_score=company.opportunity_score,
        match_score=company.match_score, combined_score=company.combined_score,
        technical_score=company.technical_score, hiring_score=company.hiring_score,
        contract_score=company.contract_score, quality_score=company.quality_score,
        contact_score=company.contact_score
    ))
    db.commit(); db.refresh(company)
    return company

async def run_campaign(campaign_id: int):
    db = SessionLocal()
    try:
        campaign = db.get(DiscoveryCampaign, campaign_id)
        if not campaign or not campaign.enabled:
            return
        run = DiscoveryRun(campaign_id=campaign.id, query=campaign.query)
        db.add(run); db.commit(); db.refresh(run)
        try:
            batch = await discover_companies(
                campaign.query, campaign.country, campaign.result_limit,
                campaign.remote_only, settings.discovery_concurrency,
            )
            saved = 0
            for result in batch.crawled:
                if "error" not in result:
                    company = save_result(db, result, " | ".join(batch.queries))
                    if company.combined_score >= campaign.minimum_score:
                        saved += 1
            run.status = "COMPLETED" if not batch.errors else "COMPLETED_WITH_ERRORS"
            run.candidates_found = len(batch.candidates)
            run.companies_saved = saved
            run.errors = "\n".join(batch.errors)
        except Exception as exc:
            logger.exception("Campaign %s failed", campaign.id)
            run.status = "FAILED"
            run.errors = str(exc)
        finally:
            run.finished_at = datetime.utcnow()
            campaign.last_run_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()

def scheduler_tick():
    db = SessionLocal()
    try:
        enabled = db.scalars(select(DiscoveryCampaign).where(DiscoveryCampaign.enabled == True)).all()
        ids = [c.id for c in enabled]
    finally:
        db.close()
    for cid in ids:
        asyncio.run(run_campaign(cid))

@app.on_event("startup")
def startup():
    db = SessionLocal()
    get_profile(db)
    db.close()
    if not scheduler.running:
        scheduler.add_job(scheduler_tick, "interval", hours=settings.discovery_schedule_hours, id="daily_campaigns", replace_existing=True)
        scheduler.start()

def render(request, name, context):
    return templates.TemplateResponse(request=request, name=name, context={"request":request, **context})

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    now = datetime.utcnow()
    stats = {
        "companies": db.scalar(select(func.count()).select_from(Company).where(Company.archived==False)) or 0,
        "high": db.scalar(select(func.count()).select_from(Company).where(Company.combined_score>=70, Company.archived==False)) or 0,
        "jobs": db.scalar(select(func.count()).select_from(Job).where(Job.is_active==True)) or 0,
        "interviews": db.scalar(select(func.count()).select_from(Company).where(Company.status=="INTERVIEW")) or 0,
        "followups": db.scalar(select(func.count()).select_from(Company).where(Company.next_follow_up_at!=None, Company.next_follow_up_at<=now+timedelta(days=7))) or 0,
    }
    recent = db.scalars(select(Company).where(Company.archived==False).order_by(desc(Company.updated_at)).limit(8)).all()
    events = db.scalars(select(ChangeEvent).order_by(desc(ChangeEvent.created_at)).limit(12)).all()
    followups = db.scalars(select(Company).where(Company.next_follow_up_at!=None, Company.next_follow_up_at<=now+timedelta(days=7)).order_by(Company.next_follow_up_at).limit(8)).all()
    dist = {
        "0-39": db.scalar(select(func.count()).select_from(Company).where(Company.combined_score<40)) or 0,
        "40-59": db.scalar(select(func.count()).select_from(Company).where(Company.combined_score.between(40,59))) or 0,
        "60-79": db.scalar(select(func.count()).select_from(Company).where(Company.combined_score.between(60,79))) or 0,
        "80-100": db.scalar(select(func.count()).select_from(Company).where(Company.combined_score>=80)) or 0,
    }
    return render(request,"dashboard.html",{"stats":stats,"recent":recent,"events":events,"followups":followups,"dist":dist})

@app.get("/companies", response_class=HTMLResponse)
def companies(request: Request, q:str="", status:str="", technology:str="", min_score:int=0, priority:int=0, sort:str="score", db:Session=Depends(get_db)):
    stmt = select(Company).where(Company.archived==False)
    if q:
        p=f"%{q}%"; stmt=stmt.where(or_(Company.name.ilike(p),Company.domain.ilike(p),Company.technologies.ilike(p),Company.notes.ilike(p)))
    if status: stmt=stmt.where(Company.status==status)
    if technology: stmt=stmt.where(Company.technologies.ilike(f"%{technology}%"))
    if priority: stmt=stmt.where(Company.priority==True)
    stmt=stmt.where(Company.combined_score>=min_score)
    order = {"score":desc(Company.combined_score),"delta":desc(Company.score_delta),"recent":desc(Company.updated_at),"name":asc(Company.name)}.get(sort,desc(Company.combined_score))
    rows=db.scalars(stmt.order_by(order)).all()
    techs=sorted({t.strip() for c in db.scalars(select(Company)).all() for t in (c.technologies or "").split(",") if t.strip()})
    return render(request,"companies.html",{"companies":rows,"statuses":STATUSES,"techs":techs,"filters":locals()})

@app.get("/companies/{company_id}", response_class=HTMLResponse)
def detail(company_id:int, request:Request, db:Session=Depends(get_db)):
    c=db.get(Company,company_id)
    if not c: raise HTTPException(404)
    histories=db.scalars(select(ScoreHistory).where(ScoreHistory.company_id==company_id).order_by(ScoreHistory.checked_at)).all()
    draft_email=build_outreach(c,get_profile(db),channel="email")
    draft_linkedin=build_outreach(c,get_profile(db),channel="linkedin")
    return render(request,"detail.html",{"company":c,"histories":histories,"statuses":STATUSES,"draft_email":draft_email,"draft_linkedin":draft_linkedin})

@app.post("/companies/add")
async def add_company(url:str=Form(...), db:Session=Depends(get_db)):
    c=save_result(db,await crawl_company(url),"Manual")
    return RedirectResponse(f"/companies/{c.id}",303)

@app.post("/companies/{company_id}/update")
def update_company(company_id:int,status:str=Form(...),notes:str=Form(""),country:str=Form(""),city:str=Form(""),employee_size:str=Form(""),priority:str|None=Form(None),next_follow_up:str=Form(""),db:Session=Depends(get_db)):
    c=db.get(Company,company_id)
    c.status=status;c.notes=notes;c.country=country;c.city=city;c.employee_size=employee_size;c.priority=priority=="on"
    c.next_follow_up_at=datetime.fromisoformat(next_follow_up) if next_follow_up else None
    db.commit()
    return RedirectResponse(f"/companies/{company_id}",303)

@app.post("/companies/{company_id}/recheck")
async def recheck(company_id:int,db:Session=Depends(get_db)):
    c=db.get(Company,company_id); save_result(db,await crawl_company(c.website),c.source_query)
    return RedirectResponse(f"/companies/{company_id}",303)

@app.post("/companies/{company_id}/github")
async def github_check(company_id:int,db:Session=Depends(get_db)):
    c=db.get(Company,company_id)
    data=await analyze_github(c.github_url)
    if data["evidence"]:
        c.evidence=(c.evidence+"\\n\\n"+data["evidence"]).strip()
        if data["languages"]:
            current={x.strip() for x in c.technologies.split(",") if x.strip()}
            current.update(data["languages"])
            c.technologies=", ".join(sorted(current))
        db.add(ChangeEvent(company_id=c.id,event_type="GITHUB",title="GitHub analyzed",details=data["evidence"],importance=1))
        db.commit()
    return RedirectResponse(f"/companies/{company_id}",303)

@app.post("/companies/{company_id}/contact")
def add_contact(company_id:int,name:str=Form(""),role:str=Form(""),email:str=Form(""),profile_url:str=Form(""),notes:str=Form(""),db:Session=Depends(get_db)):
    db.add(Contact(company_id=company_id,name=name,role=role,email=email,profile_url=profile_url,notes=notes))
    db.commit(); return RedirectResponse(f"/companies/{company_id}",303)

@app.post("/companies/{company_id}/activity")
def add_activity(company_id:int,activity_type:str=Form("NOTE"),title:str=Form(...),details:str=Form(""),db:Session=Depends(get_db)):
    c=db.get(Company,company_id)
    db.add(Activity(company_id=company_id,activity_type=activity_type,title=title,details=details))
    if activity_type in {"EMAIL","LINKEDIN","APPLICATION","CALL"}:
        c.last_contacted_at=datetime.utcnow()
        if c.status in {"NEW","HIGH_PRIORITY","REVIEW_LATER"}: c.status="CONTACTED"
    db.commit(); return RedirectResponse(f"/companies/{company_id}",303)

@app.post("/companies/{company_id}/archive")
def archive(company_id:int,db:Session=Depends(get_db)):
    c=db.get(Company,company_id); c.archived=True;db.commit()
    return RedirectResponse("/companies",303)

@app.get("/jobs", response_class=HTMLResponse)
def jobs(request:Request,q:str="",remote:int=0,min_match:int=0,db:Session=Depends(get_db)):
    stmt=select(Job).where(Job.is_active==True)
    if q: stmt=stmt.where(or_(Job.title.ilike(f"%{q}%"),Job.skills.ilike(f"%{q}%")))
    if remote: stmt=stmt.where(Job.is_remote==True)
    stmt=stmt.where(Job.match_score>=min_match).order_by(desc(Job.match_score),desc(Job.last_seen_at))
    return render(request,"jobs.html",{"jobs":db.scalars(stmt).all(),"q":q,"remote":remote,"min_match":min_match})

@app.get("/pipeline", response_class=HTMLResponse)
def pipeline(request:Request,db:Session=Depends(get_db)):
    columns={s:db.scalars(select(Company).where(Company.status==s,Company.archived==False).order_by(desc(Company.combined_score))).all() for s in PIPELINE_STATUSES}
    return render(request,"pipeline.html",{"columns":columns,"statuses":PIPELINE_STATUSES})

@app.post("/pipeline/{company_id}")
def move_pipeline(company_id:int,status:str=Form(...),db:Session=Depends(get_db)):
    c=db.get(Company,company_id);c.status=status;db.commit()
    return RedirectResponse("/pipeline",303)

@app.get("/discover", response_class=HTMLResponse)
def discover_page(request:Request,db:Session=Depends(get_db)):
    campaigns=db.scalars(select(DiscoveryCampaign).order_by(desc(DiscoveryCampaign.created_at))).all()
    return render(request,"discover.html",{"campaigns":campaigns,"results":None})

@app.post("/discover", response_class=HTMLResponse)
async def discover(request:Request,query:str=Form(...),country:str=Form(""),limit:int=Form(15),minimum_score:int=Form(0),remote_only:str|None=Form(None),save_campaign:str|None=Form(None),campaign_name:str=Form(""),db:Session=Depends(get_db)):
    output=[]
    batch = await discover_companies(query, country, limit, remote_only == "on")
    for result in batch.crawled:
        if "error" in result:
            output.append({"url":result.get("website"),"status":result["error"],"id":None})
        else:
            c=save_result(db,result," | ".join(batch.queries))
            status = f"Saved · score {c.combined_score}"
            if c.combined_score < minimum_score:
                status += f" · below campaign threshold {minimum_score}"
            output.append({"url":c.website,"status":status,"id":c.id})
    for error in batch.errors:
        output.append({"url":"Search provider","status":error,"id":None})
    run = DiscoveryRun(
        query=query, status="COMPLETED" if not batch.errors else "COMPLETED_WITH_ERRORS",
        candidates_found=len(batch.candidates), companies_saved=sum(1 for item in output if item.get("id")),
        errors="\n".join(batch.errors), finished_at=datetime.utcnow(),
    )
    db.add(run)
    if save_campaign:
        db.add(DiscoveryCampaign(
            name=campaign_name or query, query=query, country=country, result_limit=limit,
            remote_only=remote_only == "on", minimum_score=minimum_score,
        ))
    db.commit()
    campaigns=db.scalars(select(DiscoveryCampaign).order_by(desc(DiscoveryCampaign.created_at))).all()
    return render(request,"discover.html",{
        "campaigns":campaigns,"results":output,"query":query,"country":country,
        "limit":limit,"minimum_score":minimum_score,"remote_only":remote_only,
        "generated_queries":batch.queries,
    })

@app.post("/campaigns/{campaign_id}/run")
async def run_campaign_now(campaign_id:int):
    await run_campaign(campaign_id)
    return RedirectResponse("/discover",303)

@app.post("/campaigns/{campaign_id}/toggle")
def toggle_campaign(campaign_id:int,db:Session=Depends(get_db)):
    c=db.get(DiscoveryCampaign,campaign_id);c.enabled=not c.enabled;db.commit()
    return RedirectResponse("/discover",303)

@app.post("/campaigns/{campaign_id}/delete")
def delete_campaign(campaign_id:int,db:Session=Depends(get_db)):
    campaign=db.get(DiscoveryCampaign,campaign_id)
    if campaign:
        db.delete(campaign);db.commit()
    return RedirectResponse("/discover",303)

@app.get("/analytics", response_class=HTMLResponse)
def analytics(request:Request,db:Session=Depends(get_db)):
    companies=db.scalars(select(Company).where(Company.archived==False)).all()
    status_counts={}
    tech_counts={}
    country_counts={}
    for c in companies:
        status_counts[c.status]=status_counts.get(c.status,0)+1
        for t in [x.strip() for x in c.technologies.split(",") if x.strip()]:
            tech_counts[t]=tech_counts.get(t,0)+1
        if c.country: country_counts[c.country]=country_counts.get(c.country,0)+1
    top_tech=dict(sorted(tech_counts.items(),key=lambda x:x[1],reverse=True)[:12])
    top_country=dict(sorted(country_counts.items(),key=lambda x:x[1],reverse=True)[:10])
    return render(request,"analytics.html",{"status_counts":status_counts,"tech_counts":top_tech,"country_counts":top_country})

@app.get("/settings", response_class=HTMLResponse)
def settings_page(request:Request,db:Session=Depends(get_db)):
    return render(request,"settings.html",{"profile":get_profile(db)})

@app.post("/settings")
def save_settings(name:str=Form(...),headline:str=Form(...),years_experience:float=Form(...),skills:str=Form(...),preferred_roles:str=Form(...),preferred_countries:str=Form(""),preferred_work_mode:str=Form("Remote"),availability:str=Form("Immediate"),minimum_match_score:int=Form(60),email_signature:str=Form(""),db:Session=Depends(get_db)):
    p=get_profile(db)
    for k,v in locals().copy().items():
        if hasattr(p,k) and k not in {"db"}: setattr(p,k,v)
    db.commit()
    return RedirectResponse("/settings",303)

@app.post("/import")
async def import_file(file:UploadFile=File(...),db:Session=Depends(get_db)):
    text=(await file.read()).decode("utf-8",errors="ignore")
    urls=[]
    for line in text.splitlines():
        v=line.split(",")[0].strip()
        if v and v.lower() not in {"url","website","domain"}: urls.append(v)
    for result in await crawl_many(urls[:200],concurrency=4):
        if "error" not in result: save_result(db,result,"Import")
    return RedirectResponse("/companies",303)

@app.get("/export.csv")
def export_csv(db:Session=Depends(get_db)):
    rows=db.scalars(select(Company).order_by(desc(Company.combined_score))).all()
    out=io.StringIO();w=csv.writer(out)
    w.writerow(["name","domain","website","country","combined_score","opportunity_score","match_score","status","technologies","careers_url","contact_url","emails","notes"])
    for c in rows:w.writerow([c.name,c.domain,c.website,c.country,c.combined_score,c.opportunity_score,c.match_score,c.status,c.technologies,c.careers_url,c.contact_url,c.public_emails,c.notes])
    return StreamingResponse(iter([out.getvalue()]),media_type="text/csv",headers={"Content-Disposition":"attachment; filename=opportunity_radar_v3.csv"})

@app.get("/api/stats")
def api_stats(db:Session=Depends(get_db)):
    return {
        "companies":db.scalar(select(func.count()).select_from(Company)) or 0,
        "active_jobs":db.scalar(select(func.count()).select_from(Job).where(Job.is_active==True)) or 0,
        "high_matches":db.scalar(select(func.count()).select_from(Company).where(Company.combined_score>=70)) or 0,
        "due_followups":db.scalar(select(func.count()).select_from(Company).where(Company.next_follow_up_at!=None,Company.next_follow_up_at<=datetime.utcnow())) or 0,
    }

@app.get("/api/companies")
def api_companies(db:Session=Depends(get_db)):
    rows=db.scalars(select(Company).where(Company.archived==False).order_by(desc(Company.combined_score))).all()
    return [{"id":c.id,"name":c.name,"domain":c.domain,"score":c.combined_score,"opportunity_score":c.opportunity_score,"match_score":c.match_score,"status":c.status} for c in rows]


@app.get("/health")
def health():
    return {"status":"ok","version":settings.app_version,"environment":settings.environment}

@app.get("/api/discovery/runs")
def api_discovery_runs(db:Session=Depends(get_db)):
    runs=db.scalars(select(DiscoveryRun).order_by(desc(DiscoveryRun.started_at)).limit(50)).all()
    return [{"id":r.id,"query":r.query,"status":r.status,"candidates":r.candidates_found,"saved":r.companies_saved,"started_at":r.started_at.isoformat()} for r in runs]
