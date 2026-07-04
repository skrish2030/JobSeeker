import os
import json
from datetime import datetime
import contextvars
import hashlib
import re
import logging
from pymongo import MongoClient
import pymongo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("database")
logger.setLevel(logging.INFO)

IS_LAMBDA = False

# MongoDB Initialization
MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
client = MongoClient(MONGODB_URI)
db = client.jobseeker

active_user_id_var = contextvars.ContextVar("active_user_id", default="global")
active_profile_id_var = contextvars.ContextVar("active_profile_id", default="default")

default_settings = {
    "search_terms": "Software Engineer, Data Engineer, Python Developer",
    "locations": "Remote, New York, DE",
    "job_boards": "linkedin, indeed, google, zip_recruiter",
    "scrape_interval_mins": "30",
    "email_interval_hours": "1",
    "email_smtp_server": "smtp.gmail.com",
    "email_smtp_port": "587",
    "email_sender": "",
    "email_sender_password": "",
    "email_recipient": "",
    "email_alert_job_title": "",
    "email_alert_location": "",
    "resume_text": "",
    "min_relevance_score": "50",
    "scrape_country": "USA",
    "email_notifications_enabled": "false",
    "email_frequency": "daily",
    "last_emailed_time": "",
    "emailed_job_hashes": "",
    "interview_llm_provider": "ollama",
    "interview_llm_api_base": "http://localhost:11434/v1",
    "interview_llm_model": "llama3",
    "interview_llm_api_key": "",
    "ai_provider": "gemini",
    "ai_model": "gemini-2.0-flash",
    "ai_api_key": "",
    "candidate_first_name": "",
    "candidate_last_name": "",
    "candidate_email": "",
    "candidate_phone": "",
    "candidate_linkedin": "",
    "candidate_github": "",
    "candidate_portfolio": "",
    "resume_file_path": ""
}

def generate_job_id(company, title, location):
    c = re.sub(r'[^\w\s]', '', (company or "").lower().strip())
    c = re.sub(r'\s+', ' ', c)
    t = re.sub(r'[^\w\s]', '', (title or "").lower().strip())
    t = re.sub(r'\s+', ' ', t)
    l = (location or "").lower().strip()
    if "remote" in l:
        l = "remote"
    else:
        l = re.sub(r'[^\w\s]', '', l)
        l = re.sub(r'\s+', ' ', l)
    raw_str = f"{c}_{t}_{l}"
    return hashlib.md5(raw_str.encode('utf-8')).hexdigest()

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    pw_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt.hex() + ":" + pw_hash.hex()

def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt_hex, hash_hex = stored_hash.split(":")
        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(hash_hex)
        pw_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return pw_hash == expected_hash
    except Exception:
        return False

def init_db():
    logger.info("Initializing MongoDB Indexes...")
    # TTL Index for 30-day retention on jobs and history
    db.jobs.create_index([("created_at", pymongo.ASCENDING)], expireAfterSeconds=30 * 24 * 60 * 60)
    db.scrape_history.create_index([("timestamp", pymongo.ASCENDING)], expireAfterSeconds=30 * 24 * 60 * 60)
    
    # Standard Indexes
    db.users.create_index("username", unique=True)
    db.sessions.create_index("token", unique=True)
    db.jobs.create_index([("profile_id", pymongo.ASCENDING), ("job_id", pymongo.ASCENDING)], unique=True)

# --- User Auth Helpers ---
def get_user_by_username(username):
    return db.users.find_one({"username": username})

def get_user_by_id(user_id):
    return db.users.find_one({"id": user_id})

def create_user(user_id, username, email, password_hash):
    try:
        db.users.insert_one({
            "username": username,
            "id": user_id,
            "email": email,
            "password_hash": password_hash,
            "created_at": datetime.now()
        })
        return True
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return False

def save_mfa_code(user_id, code, expires_at):
    db.sessions.update_one(
        {"token": f"mfa_{user_id}"},
        {"$set": {"code": code, "expires_at": expires_at}},
        upsert=True
    )
    return True

def get_mfa_code(user_id):
    return db.sessions.find_one({"token": f"mfa_{user_id}"})

def delete_mfa_code(user_id):
    db.sessions.delete_one({"token": f"mfa_{user_id}"})
    return True

def save_pending_registration(registration_id, username, email, password_hash, code, expires_at):
    db.sessions.update_one(
        {"token": f"pending_{registration_id}"},
        {"$set": {
            "id": registration_id,
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "code": code,
            "expires_at": expires_at
        }},
        upsert=True
    )
    return True

def get_pending_registration(registration_id):
    return db.sessions.find_one({"token": f"pending_{registration_id}"})

def delete_pending_registration(registration_id):
    db.sessions.delete_one({"token": f"pending_{registration_id}"})
    return True

def create_session(token, user_id, expires_at):
    db.sessions.insert_one({"token": token, "user_id": user_id, "expires_at": expires_at})
    return True

def get_session(token):
    return db.sessions.find_one({"token": token})

def delete_session(token):
    db.sessions.delete_one({"token": token})
    return True

# --- Settings ---
def get_all_settings():
    user_id = active_user_id_var.get()
    profile_id = active_profile_id_var.get()
    key = "global" if user_id == "global" else f"{user_id}_{profile_id}"
    
    item = db.settings.find_one({"profile_id": key}, {"_id": 0})
    if not item:
        item = {"profile_id": key}
        item.update(default_settings)
        db.settings.insert_one(item)
    
    if key != "global":
        g_item = db.settings.find_one({"profile_id": "global"})
        if g_item:
            credentials_keys = ["email_smtp_server", "email_smtp_port", "email_sender", "email_sender_password", "email_recipient", "interview_llm_provider", "interview_llm_api_base", "interview_llm_model", "interview_llm_api_key", "ai_provider", "ai_model", "ai_api_key"]
            updated = False
            for k in credentials_keys:
                if not item.get(k) and g_item.get(k):
                    item[k] = g_item[k]
                    updated = True
            if updated:
                db.settings.update_one({"profile_id": key}, {"$set": item})
                
    return {k: str(v) for k, v in item.items() if k != "profile_id"}

def get_master_settings():
    item = db.settings.find_one({"profile_id": "global"}, {"_id": 0})
    if not item:
        item = {"profile_id": "global"}
        item.update(default_settings)
        db.settings.insert_one(item)
    return {k: str(v) for k, v in item.items() if k != "profile_id"}

def get_setting(key, default=""):
    return get_all_settings().get(key, default)

def update_settings(settings_dict):
    user_id = active_user_id_var.get()
    profile_id = active_profile_id_var.get()
    key = "global" if user_id == "global" else f"{user_id}_{profile_id}"
    
    db.settings.update_one({"profile_id": key}, {"$set": settings_dict}, upsert=True)
    
    if key != "global":
        credentials_keys = ["email_smtp_server", "email_smtp_port", "email_sender", "email_sender_password", "email_recipient", "interview_llm_provider", "interview_llm_api_base", "interview_llm_model", "interview_llm_api_key", "ai_provider", "ai_model", "ai_api_key"]
        sync_dict = {k: settings_dict[k] for k in credentials_keys if k in settings_dict}
        if sync_dict:
            db.settings.update_one({"profile_id": "global"}, {"$set": sync_dict}, upsert=True)

# --- Companies ---
def get_target_companies():
    user_id = active_user_id_var.get()
    profile_id = active_profile_id_var.get()
    key = "global" if user_id == "global" else f"{user_id}_{profile_id}"
    items = list(db.companies.find({"profile_id": key}))
    companies = [{"name": item["company_name"], "portal_url": item.get("portal_url")} for item in items]
    companies.sort(key=lambda x: x["name"].lower())
    return companies

def add_target_company(name, portal_url=None):
    user_id = active_user_id_var.get()
    profile_id = active_profile_id_var.get()
    key = "global" if user_id == "global" else f"{user_id}_{profile_id}"
    db.companies.update_one(
        {"profile_id": key, "company_name": name.strip()},
        {"$set": {"portal_url": portal_url.strip() if portal_url else None, "added_at": datetime.now().isoformat()}},
        upsert=True
    )

def delete_target_company(name):
    user_id = active_user_id_var.get()
    profile_id = active_profile_id_var.get()
    key = "global" if user_id == "global" else f"{user_id}_{profile_id}"
    db.companies.delete_one({"profile_id": key, "company_name": name})

# --- Jobs ---
def get_safe_score(job):
    score = job.get("score")
    if score is None: return 0
    try: return int(score)
    except: return 0

def _parse_created_at(val):
    if not val: return datetime.now()
    if isinstance(val, datetime): return val
    try: return datetime.fromisoformat(str(val))
    except: return datetime.now()

def save_raw_jobs(jobs_list):
    if not jobs_list: return 0
    new_raw_count = 0
    for job in jobs_list:
        job_id = job.get("id") or generate_job_id(job.get("company"), job.get("title"), job.get("location"))
        item = {
            "profile_id": "global",
            "job_id": job_id,
            "job_url": job.get("job_url", ""),
            "title": job.get("title", "Untitled Role"),
            "company": job.get("company", "Unknown Company"),
            "location": job.get("location", "Remote"),
            "source": job.get("source", "job_board"),
            "posted_date": job.get("posted_date", ""),
            "salary": job.get("salary", "Not disclosed"),
            "description": job.get("description", ""),
            "company_portal_url": job.get("company_portal_url"),
            "created_at": _parse_created_at(job.get("created_at"))
        }
        res = db.jobs_raw.update_one({"profile_id": "global", "job_id": job_id}, {"$setOnInsert": item}, upsert=True)
        if res.upserted_id: new_raw_count += 1
    return new_raw_count

def get_unprocessed_raw_jobs():
    raw_jobs = list(db.jobs_raw.find({"profile_id": "global"}, {"_id": 0}))
    cleaned_ids = {j["job_id"] for j in db.jobs_cleaned.find({"profile_id": "global"}, {"job_id": 1, "_id": 0})}
    return [dict(j, id=j["job_id"]) for j in raw_jobs if j["job_id"] not in cleaned_ids]

def save_cleaned_job(job):
    job_id = job.get("id") or job.get("job_id") or generate_job_id(job.get("company"), job.get("title"), job.get("location"))
    structured = job.get("structured_data", "")
    if isinstance(structured, (dict, list)): structured = json.dumps(structured)
    item = {
        "profile_id": "global",
        "job_id": job_id,
        "job_url": job.get("job_url", ""),
        "title": job.get("title", "Untitled Role"),
        "company": job.get("company", "Unknown Company"),
        "location": job.get("location", "Remote"),
        "source": job.get("source", "job_board"),
        "posted_date": job.get("posted_date", ""),
        "salary": job.get("salary", "Not disclosed"),
        "description": job.get("description", ""),
        "remote_type": job.get("remote_type", "unknown"),
        "visa_type": job.get("visa_type", "unknown"),
        "contract_type": job.get("contract_type", "unknown"),
        "score": int(job.get("score", 0)),
        "reason": job.get("reason", ""),
        "status": job.get("status", "identified"),
        "emailed": bool(job.get("emailed", False)),
        "company_portal_url": job.get("company_portal_url"),
        "structured_data": structured,
        "is_interested": bool(job.get("is_interested", False)),
        "created_at": _parse_created_at(job.get("created_at"))
    }
    db.jobs_cleaned.update_one({"profile_id": "global", "job_id": job_id}, {"$set": item}, upsert=True)
    db.jobs.update_one({"profile_id": "global", "job_id": job_id}, {"$setOnInsert": item}, upsert=True)
    return True

def save_jobs(jobs_list):
    if not jobs_list: return 0
    new_jobs_count = 0
    for job in jobs_list:
        job_id = job.get("id") or generate_job_id(job.get("company"), job.get("title"), job.get("location"))
        structured = job.get("structured_data", "")
        if isinstance(structured, (dict, list)): structured = json.dumps(structured)
        item = {
            "profile_id": "global",
            "job_id": job_id,
            "job_url": job.get("job_url", ""),
            "title": job.get("title", "Untitled Role"),
            "company": job.get("company", "Unknown Company"),
            "location": job.get("location", "Remote"),
            "source": job.get("source", "job_board"),
            "posted_date": job.get("posted_date", ""),
            "salary": job.get("salary", "Not disclosed"),
            "description": job.get("description", ""),
            "remote_type": job.get("remote_type", "unknown"),
            "visa_type": job.get("visa_type", "unknown"),
            "contract_type": job.get("contract_type", "unknown"),
            "score": int(job.get("score", 0)),
            "reason": job.get("reason", ""),
            "status": job.get("status", "identified"),
            "emailed": bool(job.get("emailed", False)),
            "company_portal_url": job.get("company_portal_url"),
            "structured_data": structured,
            "is_interested": bool(job.get("is_interested", False)),
            "created_at": _parse_created_at(job.get("created_at"))
        }
        res = db.jobs.update_one({"profile_id": "global", "job_id": job_id}, {"$setOnInsert": item}, upsert=True)
        if res.upserted_id: new_jobs_count += 1
    return new_jobs_count

def get_jobs(filters=None):
    items = list(db.jobs.find({"profile_id": "global"}, {"_id": 0}))
    jobs = []
    for item in items:
        job = dict(item)
        job["id"] = item["job_id"]
        if "created_at" in job and isinstance(job["created_at"], datetime):
            job["created_at"] = job["created_at"].isoformat()
        if filters:
            if filters.get("status") and job.get("status") != filters["status"]: continue
            if filters.get("remote_type") and job.get("remote_type") != filters["remote_type"]: continue
            if filters.get("visa_type") and job.get("visa_type") != filters["visa_type"]: continue
            if filters.get("contract_type") and job.get("contract_type") != filters["contract_type"]: continue
            if filters.get("search"):
                search_val = filters["search"].strip().lower()
                title_lower = job.get("title", "").lower()
                company_lower = job.get("company", "").lower()
                desc_lower = job.get("description", "").lower()
                if not (search_val in title_lower or search_val in company_lower or search_val in desc_lower):
                    continue
            if filters.get("min_score") and get_safe_score(job) < int(filters["min_score"]): continue
            if filters.get("is_interested") is not None and bool(job.get("is_interested", False)) != bool(filters["is_interested"]): continue
        jobs.append(job)
    jobs.sort(key=lambda x: (x.get("posted_date") or x.get("created_at") or "", get_safe_score(x)), reverse=True)
    return jobs

def get_job_by_id(job_id):
    item = db.jobs.find_one({"profile_id": "global", "job_id": job_id}, {"_id": 0})
    if item:
        item["id"] = item["job_id"]
        if "created_at" in item and isinstance(item["created_at"], datetime):
            item["created_at"] = item["created_at"].isoformat()
        return item
    return None

def update_job_status(job_id, status):
    db.jobs.update_one({"profile_id": "global", "job_id": job_id}, {"$set": {"status": status}})

def save_interested_job(job):
    job["profile_id"] = "global"
    job["job_id"] = job.get("id")
    job["is_interested"] = True
    job["created_at"] = datetime.now()
    if isinstance(job.get("structured_data"), (dict, list)):
        job["structured_data"] = json.dumps(job["structured_data"])
    db.jobs.update_one({"profile_id": "global", "job_id": job["job_id"]}, {"$set": job}, upsert=True)

def delete_interested_job(job_id):
    item = db.jobs.find_one({"profile_id": "global", "job_id": job_id})
    if item and item.get("status") in ["applied", "interviewing", "offer"]:
        db.jobs.update_one({"profile_id": "global", "job_id": job_id}, {"$set": {"is_interested": False}})
    else:
        db.jobs.delete_one({"profile_id": "global", "job_id": job_id})

def get_jobs_to_email():
    min_score = int(get_setting("min_relevance_score", "50"))
    items = list(db.jobs.find({"profile_id": "global"}, {"_id": 0}))
    jobs = []
    for item in items:
        if not item.get("emailed") and get_safe_score(item) >= min_score and item.get("status") == 'identified':
            item["id"] = item["job_id"]
            if "created_at" in item and isinstance(item["created_at"], datetime):
                item["created_at"] = item["created_at"].isoformat()
            jobs.append(item)
    jobs.sort(key=lambda x: get_safe_score(x), reverse=True)
    return jobs

def mark_jobs_as_emailed(job_ids):
    if job_ids:
        db.jobs.update_many({"profile_id": "global", "job_id": {"$in": job_ids}}, {"$set": {"emailed": True}})

# --- History ---
def log_scrape_run(jobs_found, new_jobs, status, error_message=None):
    user_id = active_user_id_var.get()
    profile_id = active_profile_id_var.get()
    key = "global" if user_id == "global" else f"{user_id}_{profile_id}"
    timestamp = datetime.now()
    db.scrape_history.insert_one({
        "profile_id": key,
        "timestamp": timestamp,
        "jobs_found": int(jobs_found),
        "new_jobs": int(new_jobs),
        "status": status,
        "error_message": error_message or ""
    })
    return timestamp.isoformat()

def update_scrape_run(run_id, jobs_found, new_jobs, status, error_message=None):
    if not run_id: return
    user_id = active_user_id_var.get()
    profile_id = active_profile_id_var.get()
    key = "global" if user_id == "global" else f"{user_id}_{profile_id}"
    db.scrape_history.update_one(
        {"profile_id": key, "timestamp": datetime.fromisoformat(run_id)},
        {"$set": {"jobs_found": int(jobs_found), "new_jobs": int(new_jobs), "status": status, "error_message": error_message or ""}}
    )

def get_scrape_history(limit=20):
    user_id = active_user_id_var.get()
    profile_id = active_profile_id_var.get()
    key = "global" if user_id == "global" else f"{user_id}_{profile_id}"
    items = list(db.scrape_history.find({"profile_id": key}).sort("timestamp", -1).limit(limit))
    
    cleaned = []
    for item in items:
        ts = item["timestamp"]
        if item.get("status") == "running" and (datetime.now() - ts).total_seconds() > 30 * 60:
            db.scrape_history.update_one({"_id": item["_id"]}, {"$set": {"status": "failed", "error_message": "Timed out"}})
            item["status"] = "failed"
            item["error_message"] = "Timed out"
        item["timestamp"] = ts.isoformat()
        item["_id"] = str(item["_id"])
        cleaned.append(item)
    return cleaned

# --- Profiles ---
def get_profiles(user_id):
    items = list(db.profiles.find({"user_id": user_id}))
    profiles = [{"id": item["profile_id"].split("_", 1)[1] if "_" in item["profile_id"] else item["profile_id"], "name": item["name"], "avatar_color": item.get("avatar_color"), "db_path": item.get("db_path", "")} for item in items]
    profiles.sort(key=lambda x: x["name"].lower())
    return profiles

def get_all_users_profiles():
    items = list(db.profiles.find({}))
    profiles = [{"id": item["profile_id"].split("_", 1)[1] if "_" in item["profile_id"] else item["profile_id"], "user_id": item["user_id"], "name": item["name"], "avatar_color": item.get("avatar_color"), "db_path": item.get("db_path", "")} for item in items]
    profiles.sort(key=lambda x: x["name"].lower())
    return profiles

def add_profile(profile_id, user_id, name, avatar_color, db_path):
    db.profiles.update_one(
        {"profile_id": f"{user_id}_{profile_id}"},
        {"$set": {"user_id": user_id, "name": name, "avatar_color": avatar_color, "db_path": db_path}},
        upsert=True
    )

def delete_profile(profile_id, user_id):
    db.profiles.delete_one({"profile_id": f"{user_id}_{profile_id}"})

def log_portal_error(company_name, portal_url, error_code, error_message):
    user_id = active_user_id_var.get()
    profile_id = active_profile_id_var.get()
    key = "global" if user_id == "global" else f"{user_id}_{profile_id}"
    db.portal_errors.insert_one({
        "profile_id": key,
        "timestamp": datetime.now(),
        "company_name": company_name,
        "portal_url": portal_url,
        "error_code": int(error_code),
        "error_message": error_message or ""
    })

def get_portal_error_logs(limit=50):
    user_id = active_user_id_var.get()
    profile_id = active_profile_id_var.get()
    key = "global" if user_id == "global" else f"{user_id}_{profile_id}"
    items = list(db.portal_errors.find({"profile_id": key}).sort("timestamp", -1).limit(limit))
    for item in items:
        item["timestamp"] = item["timestamp"].isoformat()
        item["_id"] = str(item["_id"])
    return items
