from app.services.matching import match_job
def test_matching():
 r=match_job(profile_skills="Python,FastAPI,Docker,AWS",preferred_roles="Python Developer,Backend Engineer",years_experience=5.5,preferred_work_mode="Remote",resume_text="Python FastAPI Docker AWS",job_title="Python Backend Engineer",job_description="Remote role requiring 4+ years Python FastAPI Docker.",job_skills="Python,FastAPI,Docker",is_remote=True)
 assert r.score>=80 and "python" in r.matched_skills and r.remote_alignment==100
