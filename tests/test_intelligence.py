from app.services.intelligence import analyze_company
def test_intelligence():
 r=analyze_company(text="We are hiring. Join our team. Engineering blog about Docker Kubernetes open source.",technologies=["Python","FastAPI","Docker"],jobs=[{"title":"Python Engineer"}],careers_url="/careers",github_url="https://github.com/x",contact_url="/contact",public_emails=["careers@example.com"])
 assert r.hiring_probability>=70 and r.engineering_maturity>=50 and r.outreach_probability>=50
