from __future__ import annotations

from pathlib import Path

path = Path("app/main.py")
if not path.exists():
    raise SystemExit("Run this script from the opportunity-radar repository root.")
text = path.read_text(encoding="utf-8")
original = text

replacements = [
("import asyncio, csv, io, json", "import asyncio, csv, io, json, logging"),
("from .database import Base, engine, SessionLocal", "from .config import settings\nfrom .database import Base, engine, SessionLocal\nfrom .exceptions import register_exception_handlers\nfrom .logging_config import configure_logging"),
("from .services.scheduler import scheduler", "from .services.scheduler import scheduler\nfrom .services.discovery import discover_companies"),
("Base.metadata.create_all(bind=engine)\n\napp = FastAPI(title=\"Opportunity Radar v3\")", "configure_logging()\nlogger = logging.getLogger(__name__)\nBase.metadata.create_all(bind=engine)\n\napp = FastAPI(title=settings.app_name, version=settings.app_version, debug=settings.debug)\nregister_exception_handlers(app)"),
("scheduler.add_job(scheduler_tick, \"interval\", hours=24, id=\"daily_campaigns\", replace_existing=True)", "scheduler.add_job(scheduler_tick, \"interval\", hours=settings.discovery_schedule_hours, id=\"daily_campaigns\", replace_existing=True)"),
]
for old, new in replacements:
    if old not in text:
        raise SystemExit(f"Expected main.py fragment not found:\n{old}")
    text = text.replace(old, new, 1)

old_campaign = '''async def run_campaign(campaign_id: int):
    db = SessionLocal()
    try:
        campaign = db.get(DiscoveryCampaign, campaign_id)
        if not campaign or not campaign.enabled: return
        query = f"{campaign.query} {campaign.country}".strip()
        results = list(DDGS().text(query, max_results=min(campaign.result_limit, 30)))
        urls = []
        for item in results:
            u = item.get("href") or item.get("url")
            if u and domain_from_url(u):
                urls.append(u)
        crawled = await crawl_many(urls, concurrency=4)
        for result in crawled:
            if "error" not in result:
                save_result(db, result, query)
        campaign.last_run_at = datetime.utcnow()
        db.commit()
    finally:
        db.close()
'''
new_campaign = '''async def run_campaign(campaign_id: int):
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
            run.errors = "\\n".join(batch.errors)
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
'''
if old_campaign not in text:
    raise SystemExit("Could not locate old run_campaign block.")
text = text.replace(old_campaign, new_campaign, 1)

old_discover = '''@app.post("/discover", response_class=HTMLResponse)
async def discover(request:Request,query:str=Form(...),country:str=Form(""),limit:int=Form(10),save_campaign:str|None=Form(None),campaign_name:str=Form(""),db:Session=Depends(get_db)):
    full=f"{query} {country}".strip()
    output=[]
    try:
        search=list(DDGS().text(full,max_results=min(limit,30)))
        urls=[]
        for item in search:
            u=item.get("href") or item.get("url")
            if u and domain_from_url(u): urls.append(u)
        for result in await crawl_many(urls,concurrency=4):
            if "error" in result: output.append({"url":result.get("website"),"status":result["error"],"id":None})
            else:
                c=save_result(db,result,full);output.append({"url":c.website,"status":f"Saved · score {c.combined_score}","id":c.id})
        if save_campaign:
            db.add(DiscoveryCampaign(name=campaign_name or full,query=query,country=country,result_limit=limit));db.commit()
    except Exception as exc:
        output.append({"url":"","status":f"Search failed: {exc}","id":None})
    campaigns=db.scalars(select(DiscoveryCampaign).order_by(desc(DiscoveryCampaign.created_at))).all()
    return render(request,"discover.html",{"campaigns":campaigns,"results":output,"query":query,"country":country})
'''
new_discover = '''@app.post("/discover", response_class=HTMLResponse)
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
        errors="\\n".join(batch.errors), finished_at=datetime.utcnow(),
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
'''
if old_discover not in text:
    raise SystemExit("Could not locate old discover route block.")
text = text.replace(old_discover, new_discover, 1)

anchor = '''@app.post("/campaigns/{campaign_id}/toggle")
def toggle_campaign(campaign_id:int,db:Session=Depends(get_db)):
    c=db.get(DiscoveryCampaign,campaign_id);c.enabled=not c.enabled;db.commit()
    return RedirectResponse("/discover",303)
'''
addition = anchor + '''
@app.post("/campaigns/{campaign_id}/delete")
def delete_campaign(campaign_id:int,db:Session=Depends(get_db)):
    campaign=db.get(DiscoveryCampaign,campaign_id)
    if campaign:
        db.delete(campaign);db.commit()
    return RedirectResponse("/discover",303)
'''
if anchor not in text:
    raise SystemExit("Could not locate campaign toggle route.")
text = text.replace(anchor, addition, 1)

text += '''

@app.get("/health")
def health():
    return {"status":"ok","version":settings.app_version,"environment":settings.environment}

@app.get("/api/discovery/runs")
def api_discovery_runs(db:Session=Depends(get_db)):
    runs=db.scalars(select(DiscoveryRun).order_by(desc(DiscoveryRun.started_at)).limit(50)).all()
    return [{"id":r.id,"query":r.query,"status":r.status,"candidates":r.candidates_found,"saved":r.companies_saved,"started_at":r.started_at.isoformat()} for r in runs]
'''

path.with_suffix(".py.bak").write_text(original, encoding="utf-8")
path.write_text(text, encoding="utf-8")

gitignore = Path(".gitignore")
additions = [line for line in Path(".gitignore.additions").read_text(encoding="utf-8").splitlines() if line]
current = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
missing = [line for line in additions if line not in current.splitlines()]
if missing:
    gitignore.write_text(current.rstrip() + "\n" + "\n".join(missing) + "\n", encoding="utf-8")

readme = Path("README.md")
if readme.exists():
    readme_text = readme.read_text(encoding="utf-8")
    marker = "## v0.4.0 + v0.5.0"
    if marker not in readme_text:
        readme_text += """

## v0.4.0 + v0.5.0

The project now includes environment-based configuration, logging, Alembic migrations,
tests, maintenance commands, and a multi-query discovery engine with deduplication and
campaign run history. See `INSTALL_V040_V050.md` for upgrade instructions.
"""
        readme.write_text(readme_text, encoding="utf-8")

print("Applied Opportunity Radar v0.4.0 + v0.5.0 main.py upgrade.")
