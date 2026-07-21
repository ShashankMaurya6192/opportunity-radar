from types import SimpleNamespace
from app.services.outreach_v2 import build_personalized_outreach
def test_outreach():
 p=SimpleNamespace(name="Shashank",headline="Python Backend Developer",years_experience=5.5,skills="Python,FastAPI,Docker,AWS",preferred_roles="Backend Engineer",preferred_work_mode="Remote",availability="Immediate",email_signature="Regards",resume_text="")
 j=SimpleNamespace(title="Python Engineer",skills="Python,FastAPI",location="Remote",is_remote=True,is_active=True,description="")
 c=SimpleNamespace(name="Example",technologies="Python, FastAPI",services="",description="We are hiring",evidence="",score_reasons="",careers_url="/careers",contact_url="",github_url="",public_emails="",jobs=[j])
 d=build_personalized_outreach(c,p); assert "Python Engineer" in d.subject and "FastAPI" in d.body
