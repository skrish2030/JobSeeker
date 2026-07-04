import os
import logging
import uuid
import secrets
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import FastAPI, BackgroundTasks, HTTPException, Query, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from backend.database import (
    init_db,
    get_all_settings,
    update_settings,
    get_target_companies,
    add_target_company,
    delete_target_company,
    get_jobs,
    get_job_by_id,
    update_job_status,
    save_interested_job,
    delete_interested_job,
    get_scrape_history,
    get_profiles,
    hash_password,
    verify_password,
    add_profile,
    delete_profile,
    IS_LAMBDA,
    active_user_id_var,
    active_profile_id_var,
    get_user_by_username,
    get_user_by_id,
    create_user,
    save_mfa_code,
    get_mfa_code,
    delete_mfa_code,
    save_pending_registration,
    get_pending_registration,
    delete_pending_registration,
    create_session,
    get_session,
    delete_session,
    db
)
from backend.scraper import run_scraper_cycle, run_targeted_scrape
from backend.email_service import send_jobs_digest_email, send_test_email, send_mfa_code_email
from backend.scheduler import (
    start_scheduler,
    shutdown_scheduler,
    restart_scheduler,
    get_scheduler_status
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main_server")
logger.setLevel(logging.INFO)

# Define directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

# Initialize FastAPI
app = FastAPI(title="JobSeeker Command Center API")

from prometheus_client import Counter
from prometheus_fastapi_instrumentator import Instrumentator

# Define Prometheus metrics
LOGIN_ATTEMPTS_COUNTER = Counter(
    "jobseeker_login_attempts_total",
    "Total number of login attempts",
    ["status"]
)
REGISTRATION_ATTEMPTS_COUNTER = Counter(
    "jobseeker_registration_attempts_total",
    "Total number of user registration attempts",
    ["status"]
)
MFA_VERIFICATIONS_COUNTER = Counter(
    "jobseeker_mfa_verifications_total",
    "Total number of MFA verifications",
    ["type", "status"]
)
ACTIVE_SESSIONS_COUNTER = Counter(
    "jobseeker_active_sessions_total",
    "Total number of active user sessions initialized"
)

# Initialize Instrumentator
instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_respect_env_var=False,
).instrument(app).expose(app, endpoint="/api/metrics")

from prometheus_client.core import GaugeMetricFamily, REGISTRY

class JobSeekerMetricsCollector(object):
    def collect(self):
        try:
            user_token = active_user_id_var.set("global")
            profile_token = active_profile_id_var.set("global")
            try:
                jobs = get_jobs()
                history = get_scrape_history(limit=1)
            finally:
                active_user_id_var.reset(user_token)
                active_profile_id_var.reset(profile_token)
        except Exception as e:
            logger.error(f"Failed to fetch jobs or history for metrics collector: {e}")
            jobs = []
            history = []

        # Scraper Execution Stats (Task 1)
        last_run_timestamp = 0.0
        last_run_jobs_found = 0
        last_run_new_jobs = 0
        last_run_success = 0

        if history:
            last_run = history[0]
            try:
                ts_str = last_run.get("timestamp")
                if ts_str:
                    last_run_timestamp = datetime.fromisoformat(ts_str).timestamp()
            except Exception as e:
                logger.error(f"Failed to parse last run timestamp: {e}")

            last_run_jobs_found = int(last_run.get("jobs_found") or 0)
            last_run_new_jobs = int(last_run.get("new_jobs") or 0)
            last_run_success = 1 if last_run.get("status") == "success" else 0

        # IT vs Non-IT Categorization (Task 2)
        it_count = 0
        non_it_count = 0
        
        # Recruiter vs Direct Hire Categorization
        recruiter_count = 0
        direct_hire_count = 0

        # Standard IT keywords helper
        it_keywords = [
            "software", "developer", "engineer", "programmer", "systems analyst", 
            "network", "cloud", "devops", "system admin", "systems admin", 
            "system administrator", "systems administrator", "database administrator",
            "network administrator", "cloud administrator",
            "database", "data engineer", "data scientist", "data analyst", 
            "cybersecurity", "information security", "it support", "helpdesk", "technology", 
            "tech lead", "architect", "scrum master", "product manager", "qa engineer", 
            "quality assurance", "web developer", "frontend", "backend", "fullstack", 
            "full stack", "machine learning", "ai engineer", "sre", "site reliability"
        ]

        source_counts = {}
        today_count = 0
        yesterday_count = 0
        hourly_count = 0

        now = datetime.now()
        today_date = now.date()
        yesterday_date = today_date - timedelta(days=1)
        one_hour_ago = now - timedelta(hours=1)

        import re

        for job in jobs:
            src = (job.get("source") or "").lower().strip()
            
            # Map source to standardized tags: linkedin, indeed, google, company_portal, zip_recruiter, web
            if "linkedin" in src:
                mapped_source = "linkedin"
            elif "indeed" in src:
                mapped_source = "indeed"
            elif "google" in src:
                mapped_source = "google"
            elif "company_portal" in src or "portal" in src:
                mapped_source = "company_portal"
            elif "zip_recruiter" in src or "ziprecruiter" in src:
                mapped_source = "zip_recruiter"
            else:
                mapped_source = "web"

            source_counts[mapped_source] = source_counts.get(mapped_source, 0) + 1

            # IT vs Non-IT classification
            title_lower = (job.get("title") or "").lower()
            desc_lower = (job.get("description") or "").lower()
            is_it = False
            
            if any(kw in title_lower for kw in it_keywords):
                is_it = True
            elif re.search(r'\b(it|i\.t\.)\b', title_lower):
                is_it = True
            elif any(kw in desc_lower for kw in it_keywords[:15]):
                is_it = True
                
            if is_it:
                it_count += 1
            else:
                non_it_count += 1

            # Recruiter vs Direct Hire classification
            company_lower = (job.get("company") or "").lower()
            recruiter_keywords = ["staffing", "recruiting", "solutions", "consulting", "group", "partners", "technologies", "tek", "cybercoders", "insight global", "robert half", "randstad", "apex systems", "teksystems", "kforce", "talent", "search", "headhunter", "agency"]
            is_recruiter = any(kw in company_lower for kw in recruiter_keywords)
            
            if is_recruiter:
                recruiter_count += 1
            else:
                direct_hire_count += 1

            # Timeframe classification
            created_at_str = job.get("created_at") or job.get("posted_date")
            if created_at_str:
                try:
                    dt = datetime.fromisoformat(created_at_str)
                    if dt >= one_hour_ago:
                        hourly_count += 1
                    
                    dt_date = dt.date()
                    if dt_date == today_date:
                        today_count += 1
                    elif dt_date == yesterday_date:
                        yesterday_count += 1
                except Exception:
                    try:
                        # Try parsing YYYY-MM-DD
                        dt_date = datetime.strptime(created_at_str[:10], "%Y-%m-%d").date()
                        if dt_date == today_date:
                            today_count += 1
                        elif dt_date == yesterday_date:
                            yesterday_count += 1
                    except Exception:
                        pass

        total_metric = GaugeMetricFamily("jobseeker_jobs_total", "Total jobs scraped by source tag", labels=["source"])
        for tag in ["linkedin", "indeed", "google", "company_portal", "zip_recruiter", "web"]:
            total_metric.add_metric([tag], source_counts.get(tag, 0))
        yield total_metric

        time_metric = GaugeMetricFamily("jobseeker_jobs_by_timeframe", "Number of jobs scraped by timeframe", labels=["timeframe"])
        time_metric.add_metric(["today"], today_count)
        time_metric.add_metric(["yesterday"], yesterday_count)
        time_metric.add_metric(["last_hour"], hourly_count)
        yield time_metric

        # Expose IT vs Non-IT Category Stats (Task 2)
        category_metric = GaugeMetricFamily("jobseeker_jobs_by_category", "Number of jobs by IT/Non-IT category", labels=["category"])
        category_metric.add_metric(["IT"], it_count)
        category_metric.add_metric(["Non-IT"], non_it_count)
        yield category_metric
        
        # Expose Recruiter vs Direct Hire Stats
        employer_metric = GaugeMetricFamily("jobseeker_jobs_by_employer_type", "Number of jobs by Recruiter vs Direct Hire", labels=["type"])
        employer_metric.add_metric(["Recruiter/Agency"], recruiter_count)
        employer_metric.add_metric(["Direct Hire"], direct_hire_count)
        yield employer_metric

        # Expose Scraper Run Stats (Task 1)
        yield GaugeMetricFamily("jobseeker_scraper_last_run_timestamp_seconds", "Timestamp of the last scraper run in seconds", value=last_run_timestamp)
        yield GaugeMetricFamily("jobseeker_scraper_last_run_jobs_found", "Number of jobs found in the last scraper run", value=last_run_jobs_found)
        yield GaugeMetricFamily("jobseeker_scraper_last_run_new_jobs", "Number of new jobs saved in the last scraper run", value=last_run_new_jobs)
        yield GaugeMetricFamily("jobseeker_scraper_last_run_status", "Status of the last scraper run (1=success, 0=failed/running)", value=last_run_success)

# Unregister any existing JobSeekerMetricsCollector to avoid duplication on hot reload
for collector in list(REGISTRY._collector_to_names.keys()):
    if collector.__class__.__name__ == "JobSeekerMetricsCollector":
        REGISTRY.unregister(collector)

REGISTRY.register(JobSeekerMetricsCollector())

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def db_routing_middleware(request: Request, call_next):
    path = request.url.path
    logger.info(f"[DB MIDDLEWARE] Received request: {request.method} {path} | query: {request.url.query}")
    
    # Exclude public auth endpoints, metrics, and assets
    if (
        path.startswith("/api/auth/") or 
        path == "/api/log" or
        path == "/" or 
        path == "/metrics" or
        path == "/api/metrics" or
        path.startswith("/static") or 
        request.method == "OPTIONS"
    ):

        user_token = active_user_id_var.set("global")
        profile_token = active_profile_id_var.set("global")
        try:
            return await call_next(request)
        finally:
            active_user_id_var.reset(user_token)
            active_profile_id_var.reset(profile_token)
            
    # Authenticate via Bearer Token
    auth_header = request.headers.get("authorization", "")
    user_id = None
    if auth_header.startswith("Bearer "):
        session_token = auth_header.split(" ")[1]
        session = get_session(session_token)
        if session:
            try:
                expires_at = datetime.fromisoformat(session["expires_at"])
                if expires_at > datetime.now():
                    user_id = session["user_id"]
            except Exception as e:
                logger.error(f"[DB MIDDLEWARE] Session parsing error: {e}")
                
    if not user_id:
        return JSONResponse(status_code=401, content={"detail": "Unauthorized session"})
        
    profile_id = request.headers.get("x-profile-id", "default")
    
    # Store user_id on request state so endpoints can access it
    request.state.user_id = user_id
    
    # Set context variables for request context partitioning
    user_token = active_user_id_var.set(user_id)
    profile_token = active_profile_id_var.set(profile_id)
    try:
        response = await call_next(request)
        return response
    finally:
        active_user_id_var.reset(user_token)
        active_profile_id_var.reset(profile_token)

@app.on_event("startup")
def startup_event():
    logger.info("Initializing database...")
    init_db()
    
    if not IS_LAMBDA:
        logger.info("Starting background scheduler...")
        start_scheduler()
    else:
        logger.info("Running in Lambda context. Skipping BackgroundScheduler startup to prevent execution loops and timeouts.")

@app.on_event("shutdown")
def shutdown_event():
    logger.info("Stopping background scheduler...")
    shutdown_scheduler()

# --- Pydantic Schemas ---
class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class MfaVerifyRequest(BaseModel):
    username: str
    code: str

class RegisterVerifyRequest(BaseModel):
    registration_id: str
    code: str

class SettingsUpdate(BaseModel):
    search_terms: Optional[str] = None
    locations: Optional[str] = None
    job_boards: Optional[str] = None
    scrape_interval_mins: Optional[str] = None
    email_interval_hours: Optional[str] = None
    email_smtp_server: Optional[str] = None
    email_smtp_port: Optional[str] = None
    email_sender: Optional[str] = None
    email_sender_password: Optional[str] = None
    email_recipient: Optional[str] = None
    email_alert_job_title: Optional[str] = None
    email_alert_location: Optional[str] = None
    gemini_api_key: Optional[str] = None
    resume_text: Optional[str] = None
    min_relevance_score: Optional[str] = None
    scrape_country: Optional[str] = None
    email_notifications_enabled: Optional[str] = None
    email_frequency: Optional[str] = None
    interview_llm_provider: Optional[str] = None
    interview_llm_api_base: Optional[str] = None
    interview_llm_model: Optional[str] = None
    interview_llm_api_key: Optional[str] = None
    ai_provider: Optional[str] = None
    ai_model: Optional[str] = None
    ai_api_key: Optional[str] = None
    candidate_first_name: Optional[str] = None
    candidate_last_name: Optional[str] = None
    candidate_email: Optional[str] = None
    candidate_phone: Optional[str] = None
    candidate_linkedin: Optional[str] = None
    candidate_github: Optional[str] = None
    candidate_portfolio: Optional[str] = None
    resume_file_path: Optional[str] = None


class CompanyRequest(BaseModel):
    name: str
    portal_url: Optional[str] = None

class StatusUpdateRequest(BaseModel):
    status: str

class TestEmailRequest(BaseModel):
    email: str

class FindJobsRequest(BaseModel):
    search_term: str
    location: str

class BrowserLogRequest(BaseModel):
    level: str
    message: str

# --- Auth Endpoints ---

def is_username_available(username: str) -> bool:
    if get_user_by_username(username):
        return False
    from backend.database import db
    try:
        if db.sessions.find_one({"token": {"$regex": "^pending_"}, "username": username}):
            return False
    except Exception as e:
        logger.error(f"Error checking pending registrations: {e}")
    return True

def suggest_alternative_usernames(username: str) -> list:
    import random
    suggestions = []
    suffixes = ["dev", "pro", "sre", "2026", "job", "seeker"]
    
    attempts = 0
    while len(suggestions) < 3 and attempts < 50:
        attempts += 1
        suffix = random.choice(suffixes)
        num = random.randint(10, 999)
        option1 = f"{username}{num}"
        option2 = f"{username}_{suffix}"
        option3 = f"{username}{num}_{suffix}"
        
        candidates = [option1, option2, option3]
        for cand in candidates:
            if cand not in suggestions and is_username_available(cand):
                suggestions.append(cand)
                if len(suggestions) == 3:
                    break
                    
    if len(suggestions) < 3:
        import uuid
        while len(suggestions) < 3:
            random_suffix = str(uuid.uuid4())[:4]
            cand = f"{username}_{random_suffix}"
            if cand not in suggestions and is_username_available(cand):
                suggestions.append(cand)
    return suggestions

@app.post("/api/auth/register")
def api_register(req: RegisterRequest):
    username = req.username.strip()
    email = req.email.strip()
    password = req.password
    
    if not username or not email or not password:
        REGISTRATION_ATTEMPTS_COUNTER.labels(status="failed").inc()
        raise HTTPException(status_code=400, detail="Registration fields cannot be blank")
        
    # Check if username is already taken
    if not is_username_available(username):
        alternatives = suggest_alternative_usernames(username)
        REGISTRATION_ATTEMPTS_COUNTER.labels(status="failed").inc()
        raise HTTPException(
            status_code=400, 
            detail={
                "message": "Username is already taken",
                "suggestions": alternatives
            }
        )

        
    user_id = str(uuid.uuid4())
    pw_hash = hash_password(password)
    
    # Create the user
    create_user(user_id, username, email, pw_hash)
    
    # Auto-provision Default Profile in DynamoDB
    add_profile("default", user_id, "Default Profile", "#7c4dff", "")
    
    # Create a user session
    session_token = secrets.token_hex(32)
    session_expiry = (datetime.now() + timedelta(days=30)).isoformat()
    create_session(session_token, user_id, session_expiry)
    
    # Seed all companies + portal URLs from master into new user's profile
    try:
        from backend.database import get_target_companies as get_global_companies
        # temporarily switch context to global to query master companies
        u_tok = active_user_id_var.set("global")
        p_tok = active_profile_id_var.set("global")
        master_companies = get_global_companies()
        active_user_id_var.reset(u_tok)
        active_profile_id_var.reset(p_tok)
        
        if master_companies:
            # Switch context to new user default profile
            u_tok = active_user_id_var.set(user_id)
            p_tok = active_profile_id_var.set("default")
            
            from backend.database import db
            key = f"{user_id}_default"
            added_at = datetime.now().isoformat()
            
            companies_to_insert = []
            for comp in master_companies:
                p_url = comp.get("portal_url")
                companies_to_insert.append({
                    "profile_id": key,
                    "company_name": comp["name"].strip(),
                    "portal_url": p_url.strip() if p_url else None,
                    "added_at": added_at
                })
            
            if companies_to_insert:
                db.companies.insert_many(companies_to_insert)
            
            active_user_id_var.reset(u_tok)
            active_profile_id_var.reset(p_tok)
            logger.info(f"Seeded {len(master_companies)} companies into new user's default profile in batch mode")
    except Exception as seed_err:
        logger.warning(f"Could not seed companies for new user: {seed_err}")
        
    REGISTRATION_ATTEMPTS_COUNTER.labels(status="success").inc()
    ACTIVE_SESSIONS_COUNTER.inc()
    return {
        "status": "success",
        "token": session_token,
        "username": username
    }

@app.post("/api/auth/register/verify")
def api_register_verify(req: RegisterVerifyRequest):
    code = req.code.strip()
    reg_id = req.registration_id.strip()
    
    reg = get_pending_registration(reg_id)
    if not reg or reg["code"] != code:
        MFA_VERIFICATIONS_COUNTER.labels(type="register", status="failed").inc()
        raise HTTPException(status_code=401, detail="Invalid verification code")
        
    try:
        expires_at = datetime.fromisoformat(reg["expires_at"])
        if expires_at < datetime.now():
            MFA_VERIFICATIONS_COUNTER.labels(type="register", status="failed").inc()
            raise HTTPException(status_code=401, detail="Verification code has expired")
    except Exception as e:
        logger.error(f"Expiration check error: {e}")
        raise HTTPException(status_code=500, detail="Registration session corrupt")
        
    user_id = str(uuid.uuid4())
    username = reg["username"]
    email = reg["email"]
    pw_hash = reg["password_hash"]
    
    # Create the user
    create_user(user_id, username, email, pw_hash)
    
    # Auto-provision Default Profile in DynamoDB
    add_profile("default", user_id, "Default Profile", "#7c4dff", "")
    
    # Delete the pending registration record
    delete_pending_registration(reg_id)
    
    # Create a user session
    session_token = secrets.token_hex(32)
    session_expiry = (datetime.now() + timedelta(days=30)).isoformat()
    create_session(session_token, user_id, session_expiry)
    
    # Seed all companies + portal URLs from master into new user's profile
    try:
        from backend.database import get_target_companies as get_global_companies
        # temporarily switch context to global to query master companies
        u_tok = active_user_id_var.set("global")
        p_tok = active_profile_id_var.set("global")
        master_companies = get_global_companies()
        active_user_id_var.reset(u_tok)
        active_profile_id_var.reset(p_tok)
        
        if master_companies:
            # Switch context to new user default profile
            u_tok = active_user_id_var.set(user_id)
            p_tok = active_profile_id_var.set("default")
            
            from backend.database import db
            key = f"{user_id}_default"
            added_at = datetime.now().isoformat()
            
            for comp in master_companies:
                p_url = comp.get("portal_url")
                item = {
                    "profile_id": key,
                    "company_name": comp["name"].strip(),
                    "portal_url": p_url.strip() if p_url else None,
                    "added_at": added_at
                }
                db.companies.insert_one(item)
            
            active_user_id_var.reset(u_tok)
            active_profile_id_var.reset(p_tok)
            logger.info(f"Seeded {len(master_companies)} companies into new user's default profile in batch mode")
    except Exception as seed_err:
        logger.warning(f"Could not seed companies for new user: {seed_err}")
        
    MFA_VERIFICATIONS_COUNTER.labels(type="register", status="success").inc()
    ACTIVE_SESSIONS_COUNTER.inc()
    return {
        "status": "success",
        "token": session_token,
        "username": username
    }

@app.post("/api/auth/login")
def api_login(req: LoginRequest):
    username = req.username.strip()
    password = req.password
    
    user = get_user_by_username(username)
    if not user or not verify_password(password, user["password_hash"]):
        LOGIN_ATTEMPTS_COUNTER.labels(status="failed").inc()
        raise HTTPException(status_code=401, detail="Invalid username or password")
        
    session_token = secrets.token_hex(32)
    session_expiry = (datetime.now() + timedelta(days=30)).isoformat()
    create_session(session_token, user["id"], session_expiry)
    
    LOGIN_ATTEMPTS_COUNTER.labels(status="success").inc()
    ACTIVE_SESSIONS_COUNTER.inc()
    
    return {
        "status": "success",
        "token": session_token,
        "username": username
    }

@app.post("/api/auth/mfa")
def api_verify_mfa(req: MfaVerifyRequest):
    username = req.username.strip()
    code = req.code.strip()
    
    user = get_user_by_username(username)
    if not user:
        MFA_VERIFICATIONS_COUNTER.labels(type="login", status="failed").inc()
        raise HTTPException(status_code=401, detail="User not found")
        
    mfa = get_mfa_code(user["id"])
    if not mfa or mfa["code"] != code:
        MFA_VERIFICATIONS_COUNTER.labels(type="login", status="failed").inc()
        raise HTTPException(status_code=401, detail="Invalid verification code")
        
    try:
        expires_at = datetime.fromisoformat(mfa["expires_at"])
        if expires_at < datetime.now():
            MFA_VERIFICATIONS_COUNTER.labels(type="login", status="failed").inc()
            raise HTTPException(status_code=401, detail="Verification code has expired")
    except Exception as e:
        logger.error(f"MFA validation parsing error: {e}")
        raise HTTPException(status_code=500, detail="MFA verification session corrupt")
        
    delete_mfa_code(user["id"])
    
    session_token = secrets.token_hex(32)
    session_expiry = (datetime.now() + timedelta(days=30)).isoformat()
    create_session(session_token, user["id"], session_expiry)
    
    MFA_VERIFICATIONS_COUNTER.labels(type="login", status="success").inc()
    ACTIVE_SESSIONS_COUNTER.inc()
    return {
        "status": "success",
        "token": session_token,
        "username": username
    }

# --- API Endpoints ---

@app.get("/api/jobs")
def api_get_jobs(
    status: Optional[str] = None,
    remote_type: Optional[str] = None,
    visa_type: Optional[str] = None,
    contract_type: Optional[str] = None,
    search: Optional[str] = None,
    min_score: Optional[int] = None,
    is_interested: Optional[bool] = None
):
    filters = {
        "status": status,
        "remote_type": remote_type,
        "visa_type": visa_type,
        "contract_type": contract_type,
        "search": search,
        "min_score": min_score,
        "is_interested": is_interested
    }
    all_jobs = get_jobs(filters)
    
    # Flag recommended matches based on whether search is active
    for job in all_jobs:
        job["is_recommended"] = 1 if search else 0
            
    return all_jobs[:500]

@app.get("/api/jobs/{job_id}")
def api_get_job_detail(job_id: str):
    job = get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.put("/api/jobs/{job_id}/status")
def api_update_job_status_endpoint(job_id: str, request: StatusUpdateRequest):
    valid_statuses = ["identified", "applied", "interviewing", "offer", "archived"]
    if request.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Choose from: {valid_statuses}")
    
    job = get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    update_job_status(job_id, request.status)
    return {"status": "success", "message": f"Job status updated to {request.status}"}

class ApplyRequest(BaseModel):
    mode: str = "preview"

@app.post("/api/jobs/{job_id}/apply")
def api_apply_to_job(job_id: str, request: ApplyRequest):
    if IS_LAMBDA:
        raise HTTPException(
            status_code=400, 
            detail="Auto-apply browser automation is only supported when running JobSeeker locally, due to AWS Lambda size and browser execution limits."
        )
        
    job = get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    job_url = job.get("job_url") or job.get("company_portal_url")
    if not job_url:
        raise HTTPException(status_code=400, detail="Job does not have an application URL.")
        
    settings = get_all_settings()
    
    if not settings.get("candidate_email") or not settings.get("candidate_first_name"):
         raise HTTPException(
             status_code=400, 
             detail="Auto-Apply profile details are incomplete. Configure First Name and Email under the 'Profile & CV' tab in Settings."
         )
         
    from backend.auto_applier import run_auto_apply
    res = run_auto_apply(job_url, job.get("company", "Company"), settings, mode=request.mode)
    
    if res.get("status") in ["success", "preview"]:
        update_job_status(job_id, "applied")
        return {"status": "success", "message": res.get("message")}
    else:
        raise HTTPException(status_code=500, detail=res.get("message", "Auto-apply failed."))


@app.post("/api/jobs/interested")
def api_save_interested_job(job: dict):
    if not job.get("id"):
        raise HTTPException(status_code=400, detail="Job must have an 'id'")
    save_interested_job(job)
    return {"status": "success", "message": "Job marked as interested"}

@app.delete("/api/jobs/interested/{job_id}")
def api_delete_interested_job(job_id: str):
    delete_interested_job(job_id)
    return {"status": "success", "message": "Job unmarked as interested"}

@app.get("/api/settings")
def api_get_settings(request: Request):
    user_id = request.state.user_id
    user = get_user_by_id(user_id)
    user_email = user["email"] if user else ""
        
    settings = get_all_settings()
    
    # Auto-initialize email_recipient if empty
    if not settings.get("email_recipient") and user_email:
        settings["email_recipient"] = user_email
        try:
            update_settings({"email_recipient": user_email})
        except Exception as e:
            logger.error(f"Failed to auto-save recipient email: {e}")
            
    # Mask credentials
    sensitive_keys = ["email_sender_password", "interview_llm_api_key"]
    for k in sensitive_keys:
        if settings.get(k):
            settings[k] = "********"
            
    return settings

@app.post("/api/settings")
def api_update_settings(settings: SettingsUpdate):
    settings_dict = {k: v for k, v in settings.model_dump().items() if v is not None}
    
    # Prevent overwriting database settings with masked values
    sensitive_keys = ["email_sender_password", "interview_llm_api_key"]
    for k in sensitive_keys:
        if settings_dict.get(k) == "********":
            settings_dict.pop(k, None)
            
    update_settings(settings_dict)
    
    try:
        restart_scheduler()
    except Exception as e:
        logger.error(f"Failed to reload scheduler settings: {str(e)}")
        
    res_settings = get_all_settings()
    for k in sensitive_keys:
        if res_settings.get(k):
            res_settings[k] = "********"
            
    return {"status": "success", "settings": res_settings}

@app.get("/api/target-companies")
def api_get_companies():
    return get_target_companies()

@app.post("/api/target-companies")
def api_add_company(request: CompanyRequest):
    if not request.name.strip():
        raise HTTPException(status_code=400, detail="Company name cannot be blank")
    add_target_company(request.name, request.portal_url)
    return {"status": "success", "companies": get_target_companies()}

@app.delete("/api/target-companies/{name}")
def api_delete_company(name: str):
    delete_target_company(name)
    return {"status": "success", "companies": get_target_companies()}

# Background scraper execution
def bg_scrape_task():
    logger.info("Manual scrape triggered in background...")
    try:
        run_scraper_cycle()
    except Exception as e:
        logger.error(f"Manual scrape background job failed: {str(e)}")

@app.post("/api/scrape/now")
def api_trigger_scrape(background_tasks: BackgroundTasks):
    if IS_LAMBDA:
        try:
            logger.info("[SCRAPE NOW] Invoking scraper Lambda asynchronously for manual scrape")
            import json
            client = boto3.client("lambda")
            client.invoke(
                FunctionName="jobseeker-scraper",
                InvocationType="Event",
                Payload=json.dumps({})
            )
            return {"status": "success", "message": "Manual scrape triggered in the background. Results will load in a minute."}
        except Exception as e:
            logger.error(f"[SCRAPE NOW] Failed to invoke scraper Lambda: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to trigger background scraper: {str(e)}")
    else:
        background_tasks.add_task(bg_scrape_task)
        return {"status": "success", "message": "Job scraper initiated in the background. Results will load in a minute."}

def bg_scrape_and_process_task(search_term: str, location: str, user_id: str, profile_id: str):
    user_token = active_user_id_var.set(user_id)
    profile_token = active_profile_id_var.set(profile_id)
    try:
        logger.info(f"[SEARCH SCRAPE] Background scrape and process started for '{search_term}' (User: {user_id}, Profile: {profile_id})...")
        from backend.scraper import run_targeted_scrape, process_raw_jobs_batch
        run_targeted_scrape(search_term, location)
        process_raw_jobs_batch()
        logger.info(f"[SEARCH SCRAPE] Background scrape and process completed for '{search_term}'")
    except Exception as e:
        logger.error(f"[SEARCH SCRAPE] Background scrape and process failed: {e}")
    finally:
        active_user_id_var.reset(user_token)
        active_profile_id_var.reset(profile_token)

@app.post("/api/scrape/find")
def api_trigger_find_jobs(request: FindJobsRequest, background_tasks: BackgroundTasks):
    search_term = request.search_term.strip()
    location = request.location.strip()
    
    user_id = active_user_id_var.get()
    profile_id = active_profile_id_var.get()
    
    if search_term or location:
        if IS_LAMBDA:
            try:
                logger.info(f"[SEARCH SCRAPE] Invoking scraper Lambda asynchronously for '{search_term}' in '{location}'")
                import json
                client = boto3.client("lambda")
                payload = {
                    "search_term": search_term,
                    "location": location
                }
                client.invoke(
                    FunctionName="jobseeker-scraper",
                    InvocationType="Event",
                    Payload=json.dumps(payload)
                )
            except Exception as e:
                logger.error(f"[SEARCH SCRAPE] Failed to invoke scraper Lambda: {e}")
        else:
            background_tasks.add_task(bg_scrape_and_process_task, search_term, location, user_id, profile_id)

        
    try:
        # Fetch all matching jobs from database (post-filters applied inside get_jobs)
        filters = {
            "search": search_term,
        }
        recommended_jobs = get_jobs(filters)
        
        # Apply location filter
        if location:
            loc_lower = location.lower()
            filtered_by_loc = []
            for job in recommended_jobs:
                job_loc = (job.get("location") or "").lower()
                if loc_lower in job_loc or ("remote" in job_loc and loc_lower == "remote"):
                    filtered_by_loc.append(job)
            recommended_jobs = filtered_by_loc
            
        # Flag recommended search matches
        for job in recommended_jobs:
            job["is_recommended"] = 1
            
        if search_term:
            logger.info(f"Targeted search for '{search_term}' in '{location}' returned {len(recommended_jobs)} matches.")
            return recommended_jobs[:100]
        else:
            # If search term is empty, return settings-recommended matches first, followed by others
            all_jobs = get_jobs()
            rec_ids = {j["id"] for j in recommended_jobs}
            other_jobs = []
            for j in all_jobs:
                if j["id"] not in rec_ids:
                    j["is_recommended"] = 0
                    other_jobs.append(j)
            combined = recommended_jobs + other_jobs
            logger.info(f"Empty search returned {len(recommended_jobs)} settings matches and {len(other_jobs)} other jobs.")
            return combined[:100]
            
    except Exception as e:
        logger.error(f"Targeted search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Targeted search failed: {str(e)}")

class AiJobInput(BaseModel):
    title: str
    company: str
    description: str

@app.post("/api/jobs/ai/tailor")
def api_tailor_job(
    req: AiJobInput,
    x_ai_provider: Optional[str] = Header(None, alias="X-AI-Provider"),
    x_ai_model: Optional[str] = Header(None, alias="X-AI-Model"),
    x_ai_api_key: Optional[str] = Header(None, alias="X-AI-API-Key")
):
    settings = get_all_settings()
    provider = settings.get("ai_provider") or x_ai_provider
    model = settings.get("ai_model") or x_ai_model
    api_key = settings.get("ai_api_key") or x_ai_api_key
    
    if not provider or not api_key:
        raise HTTPException(status_code=400, detail="AI Provider, Model, and API Key must be configured in settings.")
    
    resume_text = settings.get("resume_text", "")
    
    from backend.ai_engine import generate_cv_tailoring_with_ai
    res = generate_cv_tailoring_with_ai(
        title=req.title,
        company=req.company,
        description=req.description,
        resume_text=resume_text,
        provider=provider,
        model=model,
        api_key=api_key
    )
    if isinstance(res, dict) and res.get("status") == "error":
        raise HTTPException(status_code=500, detail=res.get("error", "AI CV Tailoring failed"))
    return res

@app.post("/api/jobs/ai/cover-letter")
def api_cover_letter_job(
    req: AiJobInput,
    x_ai_provider: Optional[str] = Header(None, alias="X-AI-Provider"),
    x_ai_model: Optional[str] = Header(None, alias="X-AI-Model"),
    x_ai_api_key: Optional[str] = Header(None, alias="X-AI-API-Key")
):
    settings = get_all_settings()
    provider = settings.get("ai_provider") or x_ai_provider
    model = settings.get("ai_model") or x_ai_model
    api_key = settings.get("ai_api_key") or x_ai_api_key
    
    if not provider or not api_key:
        raise HTTPException(status_code=400, detail="AI Provider, Model, and API Key must be configured in settings.")
        
    resume_text = settings.get("resume_text", "")
    
    from backend.ai_engine import generate_cover_letter_with_ai
    res = generate_cover_letter_with_ai(
        title=req.title,
        company=req.company,
        description=req.description,
        resume_text=resume_text,
        provider=provider,
        model=model,
        api_key=api_key
    )
    if isinstance(res, dict) and res.get("status") == "error":
        raise HTTPException(status_code=500, detail=res.get("error", "AI Cover Letter failed"))
    return res

@app.post("/api/jobs/ai/mock-interview")
def api_mock_interview_job(
    req: AiJobInput,
    x_ai_provider: Optional[str] = Header(None, alias="X-AI-Provider"),
    x_ai_model: Optional[str] = Header(None, alias="X-AI-Model"),
    x_ai_api_key: Optional[str] = Header(None, alias="X-AI-API-Key")
):
    settings = get_all_settings()
    provider = settings.get("ai_provider") or x_ai_provider
    model = settings.get("ai_model") or x_ai_model
    api_key = settings.get("ai_api_key") or x_ai_api_key
    
    if not provider or not api_key:
        raise HTTPException(status_code=400, detail="AI Provider, Model, and API Key must be configured in settings.")
        
    resume_text = settings.get("resume_text", "")
    
    from backend.ai_engine import generate_interview_prep_with_ai
    res = generate_interview_prep_with_ai(
        title=req.title,
        company=req.company,
        description=req.description,
        resume_text=resume_text,
        provider=provider,
        model=model,
        api_key=api_key
    )
    if isinstance(res, dict) and res.get("status") == "error":
        raise HTTPException(status_code=500, detail=res.get("error", "AI Mock Interview Prep failed"))
    return res

@app.post("/api/jobs/ai/outreach-templates")
def api_outreach_templates_job(
    req: AiJobInput,
    x_ai_provider: Optional[str] = Header(None, alias="X-AI-Provider"),
    x_ai_model: Optional[str] = Header(None, alias="X-AI-Model"),
    x_ai_api_key: Optional[str] = Header(None, alias="X-AI-API-Key")
):
    settings = get_all_settings()
    provider = settings.get("ai_provider") or x_ai_provider
    model = settings.get("ai_model") or x_ai_model
    api_key = settings.get("ai_api_key") or x_ai_api_key
    
    if not provider or not api_key:
        raise HTTPException(status_code=400, detail="AI Provider, Model, and API Key must be configured in settings.")
        
    resume_text = settings.get("resume_text", "")
    
    from backend.ai_engine import generate_outreach_templates_with_ai
    res = generate_outreach_templates_with_ai(
        title=req.title,
        company=req.company,
        description=req.description,
        resume_text=resume_text,
        provider=provider,
        model=model,
        api_key=api_key
    )
    if isinstance(res, dict) and res.get("status") == "error":
        raise HTTPException(status_code=500, detail=res.get("error", "AI Outreach Templates failed"))
    return res


class InterviewChatRequest(BaseModel):
    title: str
    company: str
    description: str
    conversation_history: list = []

@app.post("/api/jobs/ai/interview-chat")
def api_interview_chat(
    req: InterviewChatRequest,
    x_ai_provider: Optional[str] = Header(None, alias="X-AI-Provider"),
    x_ai_model: Optional[str] = Header(None, alias="X-AI-Model"),
    x_ai_api_key: Optional[str] = Header(None, alias="X-AI-API-Key")
):
    settings = get_all_settings()
    provider = settings.get("ai_provider") or x_ai_provider
    model = settings.get("ai_model") or x_ai_model
    api_key = settings.get("ai_api_key") or x_ai_api_key
    
    if not provider or not api_key:
        raise HTTPException(status_code=400, detail="AI Provider, Model, and API Key must be configured in settings.")
        
    history = req.conversation_history
    question_count = sum(1 for m in history if m.get("role") == "assistant")
    MAX_QUESTIONS = 8
    
    if question_count == 0:
        prompt = f"""You are a senior technical interviewer and career mentor with over 30 years of experience. Your goal is to guide the candidate at {req.company} for the role: {req.title}, helping them learn and succeed in getting this job.
Job Description: {req.description[:1500]}
Introduce yourself in 1-2 sentences, then ask the first relevant technical/behavioral question. Ask only ONE question."""
    elif question_count >= MAX_QUESTIONS:
        convo = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in history[-16:]])
        prompt = f"""You are a senior technical interviewer and career mentor with over 30 years of experience who has been interviewing the candidate for the role {req.title} at {req.company}.
Interview transcript:\n{convo}\n\nProvide: 1) Overall score (X/100) 2) 3 strengths 3) 2-3 improvement areas 4) Hiring recommendation. Be honest and constructive, helping them learn how to improve and get the job."""
    else:
        convo = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in history])
        prompt = f"""You are a senior technical interviewer and career mentor with over 30 years of experience. Interviewing candidate for {req.title} at {req.company}.
Transcript:\n{convo}\n\nThis was Q{question_count}/{MAX_QUESTIONS}. Give 2-3 sentences of honest feedback on the last answer, then ask Q{question_count+1} - a new, specific question for this role. Ask only ONE question."""

    from backend.ai_engine import call_ai_model
    response_text = call_ai_model(prompt, provider, model, api_key, expect_json=False)
    
    if isinstance(response_text, dict) and response_text.get("error"):
        raise HTTPException(status_code=500, detail=response_text["error"])
        
    if question_count >= MAX_QUESTIONS:
        return {
            "message": f"Interview complete! Your performance summary:\n\n{response_text}",
            "is_done": True,
            "summary": {
                "score": f"Complete ({question_count} questions)",
                "feedback": response_text
            }
        }
    else:
        return {
            "message": response_text,
            "is_done": False,
            "summary": None
        }

class BuildResumeRequest(BaseModel):
    title: str
    company: str
    description: str
    user_experience: str

@app.post("/api/jobs/ai/build-resume")
def api_build_resume(
    req: BuildResumeRequest,
    x_ai_provider: Optional[str] = Header(None, alias="X-AI-Provider"),
    x_ai_model: Optional[str] = Header(None, alias="X-AI-Model"),
    x_ai_api_key: Optional[str] = Header(None, alias="X-AI-API-Key")
):
    settings = get_all_settings()
    provider = settings.get("ai_provider") or x_ai_provider
    model = settings.get("ai_model") or x_ai_model
    api_key = settings.get("ai_api_key") or x_ai_api_key
    
    if not provider or not api_key:
        raise HTTPException(status_code=400, detail="AI Provider, Model, and API Key must be configured in settings.")
        
    prompt = f"""You are a senior executive resume writer and mentor with over 30 years of experience. Create an ATS-optimized resume tailored for the following role, helping the candidate stand out and get this job.

TARGET ROLE: {req.title} at {req.company}
JOB DESCRIPTION: {req.description[:2500]}
CANDIDATE BACKGROUND: {req.user_experience[:2500]}

Return EXACTLY this format with no other text:

SUMMARY:
[2-3 sentence professional summary tailored to the role]

SKILLS:
[12-18 relevant technical and soft skills, comma-separated]

EXPERIENCE:
[Work history with role, company, dates, 3-4 tailored achievement bullets each. Quantify impact wherever possible.]

EDUCATION:
[Education details]

Tailor every bullet to the job description. Use strong action verbs. Make it specific to {req.company}."""
    
    from backend.ai_engine import call_ai_model
    full_text = call_ai_model(prompt, provider, model, api_key, expect_json=False)
    
    if isinstance(full_text, dict) and full_text.get("error"):
        raise HTTPException(status_code=500, detail=full_text["error"])
        
    import re
    sections = {}
    patterns = {
        "summary": r"SUMMARY:\s*([\s\S]*?)(?=SKILLS:|EXPERIENCE:|EDUCATION:|$)",
        "skills": r"SKILLS:\s*([\s\S]*?)(?=SUMMARY:|EXPERIENCE:|EDUCATION:|$)",
        "experience": r"EXPERIENCE:\s*([\s\S]*?)(?=SUMMARY:|SKILLS:|EDUCATION:|$)",
        "education": r"EDUCATION:\s*([\s\S]*?)(?=SUMMARY:|SKILLS:|EXPERIENCE:|$)",
    }
    for key, pattern in patterns.items():
        m = re.search(pattern, full_text, re.IGNORECASE)
        if m:
            sections[key] = m.group(1).strip()
    return {"resume_text": full_text, "sections": sections}

@app.post("/api/email/now")
def api_trigger_email():
    try:
        sent_count = send_jobs_digest_email(force_db_only=True)
        return {"status": "success", "message": f"Email dispatch completed. Sent {sent_count} jobs."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email dispatch failed: {str(e)}")

@app.post("/api/email/test")
def api_trigger_test_email(request: TestEmailRequest):
    try:
        send_test_email(request.email)
        return {"status": "success", "message": f"Test email sent successfully to {request.email}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test email failed: {str(e)}")

@app.get("/api/status")
def api_get_status():
    scheduler_info = get_scheduler_status()
    history = get_scrape_history(15)
    return {
        "scheduler": scheduler_info,
        "scrape_history": history
    }

@app.get("/api/scrape/status")
def api_get_scrape_status():
    history = get_scrape_history(1)
    if history and history[0].get("status") == "running":
        try:
            ts_str = history[0].get("timestamp")
            ts = datetime.fromisoformat(ts_str)
            now = datetime.now()
            diff_mins = (now - ts).total_seconds() / 60.0
            if diff_mins < 30:
                return {"in_progress": True}
        except Exception:
            return {"in_progress": True}
    return {"in_progress": False}

@app.get("/api/portal-errors")
def api_get_portal_errors():
    from backend.database import get_portal_error_logs
    return get_portal_error_logs()

# --- Profiles Management Endpoints ---

class ProfileCreateRequest(BaseModel):
    name: str
    avatar_color: Optional[str] = "#7c4dff"

@app.get("/api/profiles")
def api_get_profiles(request: Request):
    user_id = request.state.user_id
    return get_profiles(user_id)

@app.post("/api/profiles")
def api_create_profile(request: Request, profile_req: ProfileCreateRequest):
    user_id = request.state.user_id
    name = profile_req.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Profile name cannot be blank")
        
    import re
    profile_id = re.sub(r'[^\w\s-]', '', name.lower().strip())
    profile_id = re.sub(r'[\s_-]+', '-', profile_id)
    
    if profile_id == "default":
        raise HTTPException(status_code=400, detail="Name cannot be 'default'")
        
    profiles = get_profiles(user_id)
    if any(p["id"] == profile_id for p in profiles):
        raise HTTPException(status_code=400, detail="Profile with this name already exists")
        
    add_profile(profile_id, user_id, name, profile_req.avatar_color, "")
    return {"status": "success", "profiles": get_profiles(user_id)}

@app.delete("/api/profiles/{profile_id}")
def api_delete_profile(request: Request, profile_id: str):
    user_id = request.state.user_id
    if profile_id == "default":
        raise HTTPException(status_code=400, detail="Cannot delete default profile")
        
    profiles = get_profiles(user_id)
    matching_profile = next((p for p in profiles if p["id"] == profile_id), None)
    if not matching_profile:
        raise HTTPException(status_code=404, detail="Profile not found")
        
    delete_profile(profile_id, user_id)
    return {"status": "success", "profiles": get_profiles(user_id)}

@app.post("/api/log")
def api_browser_log(req: BrowserLogRequest):
    logger.info(f"[BROWSER CONSOLE {req.level.upper()}] {req.message}")
    return {"status": "success"}

# Serve the static UI files
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
    
    @app.get("/")
    def serve_frontend():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
else:
    @app.get("/")
    def fallback_api_info():
        return {"message": "JobSeeker Command Center backend running. Static UI files folder 'frontend' not found."}



# --- Market Analyst Insights Endpoint ---
@app.get("/api/market-insights")
def api_get_market_insights():
    try:
        from backend.database import db, get_all_settings
        from backend.ai_engine import generate_market_insights_with_ai
        
        # 1. Aggregate top 5 job titles from local database (filtering out garbage)
        pipeline = [
            {"$match": {
                "title": {
                    "$nin": [None, "", " ", "Careers", "Job Search", "Job", "Jobs"],
                    "$not": {"$regex": "^(?i)(careers|job search|jobs?)$"}
                }
            }},
            {"$group": {"_id": "$title", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]
        top_jobs = list(db.jobs.aggregate(pipeline))
        job_stats = "\n".join([f"- {job['_id']}: {job['count']} jobs" for job in top_jobs])
        if not job_stats:
            job_stats = "No jobs found in database yet. Assume general software engineering market."
            
        # 2. Call AI
        settings = get_all_settings()
        ai_provider = settings.get("ai_provider", "gemini")
        ai_model = settings.get("ai_model", "gemini-2.0-flash")
        ai_api_key = settings.get("ai_api_key", "")
        
        ai_response = generate_market_insights_with_ai(job_stats, ai_provider, ai_model, ai_api_key)
        
        # 3. Fetch YouTube Videos
        youtube_videos = []
        try:
            from youtubesearchpython import VideosSearch
            for query in ai_response.get("youtube_queries", []):
                videosSearch = VideosSearch(query, limit = 1)
                res = videosSearch.result()
                if res and res.get("result"):
                    vid = res["result"][0]
                    youtube_videos.append({
                        "title": vid.get("title"),
                        "link": vid.get("link"),
                        "thumbnail": vid.get("thumbnails", [{}])[0].get("url"),
                        "channel": vid.get("channel", {}).get("name")
                    })
        except Exception as e:
            logger.error(f"Failed to fetch YouTube videos: {e}")
            
        return {
            "status": "success",
            "stats": top_jobs,
            "analysis": ai_response,
            "videos": youtube_videos
        }
    except Exception as e:
        logger.error(f"Market Insights Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
