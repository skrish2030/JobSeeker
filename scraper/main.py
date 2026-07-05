import os
import logging
import hashlib
from datetime import datetime
from supabase import create_client, Client
from jobspy import scrape_jobs
import json
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gh_scraper")

def get_supabase() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
    return create_client(url, key)

def calculate_local_score(title: str, desc: str, target_keywords: list) -> int:
    """Smart local scoring logic (0-100) based on heuristics, replacing AI."""
    score = 50
    title_lower = title.lower()
    desc_lower = desc.lower()
    
    # Boost for exact keyword matches in title
    for kw in target_keywords:
        if kw.lower() in title_lower:
            score += 25
            break
            
    # Boost for common modern tech stack in desc
    tech_stack = ["react", "node", "python", "aws", "typescript", "docker", "kubernetes", "sql", "postgres", "next.js", "tailwind"]
    matches = sum(1 for tech in tech_stack if tech in desc_lower)
    score += (matches * 3)
    
    return max(0, min(100, score))

def run_scraper():
    supabase = get_supabase()
    
    # Target keywords and locations from user settings
    settings_res = supabase.table("user_settings").select("target_job_title, target_location").execute()
    
    # We want a massive generalized pool, so we start with a huge baseline
    broad_keywords = [
        "Software Engineer", "Frontend Developer", "Backend Developer", "Full Stack", 
        "Data Scientist", "Data Engineer", "Machine Learning", "DevOps", 
        "Product Manager", "Project Manager", "UX Designer", "UI Designer",
        "Marketing Manager", "Sales Manager", "Account Executive", "Business Analyst",
        "Registered Nurse", "Healthcare Administration", "Financial Analyst", "Accountant",
        "Operations Manager", "Customer Success"
    ]
    broad_locations = [
        "Remote", "New York, NY", "San Francisco, CA", "Austin, TX", "Seattle, WA", 
        "Chicago, IL", "Boston, MA", "Los Angeles, CA", "Denver, CO", "Atlanta, GA", "Remote USA"
    ]
    
    keywords = list(broad_keywords)
    locations = list(broad_locations)
    
    if settings_res.data:
        user_kws = [s["target_job_title"] for s in settings_res.data if s.get("target_job_title")]
        user_locs = [s["target_location"] for s in settings_res.data if s.get("target_location")]
        keywords.extend(user_kws)
        locations.extend(user_locs)
        
    keywords = list(set(keywords))
    locations = list(set(locations))
    
    # Automatically append "Intern" to the keywords so the Internships tab gets populated
    intern_keywords = [f"{kw} Intern" for kw in keywords]
    keywords.extend(intern_keywords)
    keywords = list(set(keywords))
    
    # Create log entry
    log_res = supabase.table("scrape_log").insert({
        "run_id": os.environ.get("GITHUB_RUN_ID", "local"),
        "notes": f"Scraping for {len(keywords)} keywords in {len(locations)} locations using Local Heuristics"
    }).execute()
    log_id = log_res.data[0]["id"]
    
    jobs_inserted = 0
    errors_count = 0
        
    for location in locations:
        for kw in keywords:
            logger.info(f"Scraping '{kw}' in '{location}'...")
            try:
                df = scrape_jobs(
                    site_name=["indeed", "linkedin", "glassdoor", "ziprecruiter", "google"],
                    search_term=kw,
                    location=location,
                    results_wanted=500,
                    hours_old=72,
                    country_indeed="usa"
                )
                
                if df is None or df.empty:
                    continue
                    
                for _, row in df.iterrows():
                    job_url = row.get("job_url") or row.get("job_url_direct") or ""
                    if not job_url:
                        continue
                        
                    title = row.get("title") or "Untitled"
                    company = row.get("company") or "Unknown"
                    loc = row.get("location") or location
                    
                    # Hash for deduplication
                    hash_str = f"{title}-{company}-{loc}".lower()
                    job_hash = hashlib.md5(hash_str.encode('utf-8')).hexdigest()
                    
                    # Check if exists
                    existing = supabase.table("jobs").select("id").eq("job_hash", job_hash).execute()
                    if existing.data:
                        continue
                    
                    desc = row.get("description") or ""
                    
                    # Smart Local Scoring
                    score = calculate_local_score(title, desc, keywords)
                    
                    # Insert job
                    job_data = {
                        "job_hash": job_hash,
                        "title": title,
                        "company": company,
                        "location": loc,
                        "source_site": row.get("site", "unknown"),
                        "job_url": job_url,
                        "description": desc,
                        "min_amount": row.get("min_amount"),
                        "max_amount": row.get("max_amount"),
                        "currency": row.get("currency"),
                        "interval": row.get("interval"),
                        "score": score,
                        "posted_date": str(row.get("date_posted")) if pd.notna(row.get("date_posted")) else None
                    }
                    
                    # Handle pandas NaN which JSON can't serialize
                    for k, v in job_data.items():
                        if pd.isna(v):
                            job_data[k] = None
                            
                    try:
                        supabase.table("jobs").insert(job_data).execute()
                        jobs_inserted += 1
                    except Exception as insert_e:
                        logger.error(f"Failed to insert job {title}: {insert_e}")
                        errors_count += 1
                        
            except Exception as e:
                logger.error(f"Scraper failed for {kw} in {location}: {e}")
                errors_count += 1
            
    # Update log
    supabase.table("scrape_log").update({
        "finished_at": datetime.utcnow().isoformat(),
        "jobs_inserted": jobs_inserted,
        "errors_count": errors_count
    }).eq("id", log_id).execute()
    
    logger.info(f"Scrape cycle complete. Inserted {jobs_inserted} jobs with {errors_count} errors.")

if __name__ == "__main__":
    run_scraper()
