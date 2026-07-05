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
    
    import random
    import time
    
    # Ultra-stealthy mode: Pick 1 random site, 1 random location, and 2 random keywords per run
    available_sites = ["indeed", "linkedin", "glassdoor", "zip_recruiter", "google"]
    target_site = random.choice(available_sites)
    
    random.shuffle(locations)
    random.shuffle(keywords)
    target_locations = locations[:1]
    target_keywords = keywords[:2]
        
    for location in target_locations:
        for kw in target_keywords:
            logger.info(f"Scraping '{kw}' in '{location}' on {target_site}...")
            try:
                df = scrape_jobs(
                    site_name=[target_site],
                    search_term=kw,
                    location=location,
                    results_wanted=50, # Keep results small per request to avoid pagination bans
                    hours_old=72,
                    country_indeed="usa"
                )
                
                # Slow and steady delay to mimic human behavior
                time.sleep(15)
                
                if df is None or df.empty:
                    continue
                    
                # Prepare all hashes for this batch
                batch_jobs = []
                for _, row in df.iterrows():
                    job_url = row.get("job_url") or row.get("job_url_direct") or ""
                    if not job_url:
                        continue
                    
                    title = row.get("title") or "Untitled"
                    company = row.get("company") or "Unknown"
                    loc = row.get("location") or location
                    hash_str = f"{title}-{company}-{loc}".lower()
                    job_hash = hashlib.md5(hash_str.encode('utf-8')).hexdigest()
                    
                    batch_jobs.append({
                        "job_hash": job_hash,
                        "title": title,
                        "company": company,
                        "location": loc,
                        "row_data": row,
                        "job_url": job_url
                    })
                    
                if not batch_jobs:
                    continue
                    
                # 1. BULK FETCH: Check all hashes at once to save API calls
                all_hashes = [b["job_hash"] for b in batch_jobs]
                existing_hashes = set()
                # Break into chunks of 100 for the IN clause to avoid URL length limits
                for i in range(0, len(all_hashes), 100):
                    chunk = all_hashes[i:i+100]
                    res = supabase.table("jobs").select("job_hash").in_("job_hash", chunk).execute()
                    if res.data:
                        existing_hashes.update([r["job_hash"] for r in res.data])
                        
                # 2. FILTER: Keep only new jobs
                new_jobs_to_insert = []
                for b in batch_jobs:
                    if b["job_hash"] in existing_hashes:
                        continue
                        
                    row = b["row_data"]
                    desc = row.get("description") or ""
                    score = calculate_local_score(b["title"], desc, keywords)
                    
                    job_data = {
                        "job_hash": b["job_hash"],
                        "title": b["title"],
                        "company": b["company"],
                        "location": b["location"],
                        "source_site": row.get("site", "unknown"),
                        "job_url": b["job_url"],
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
                        if pd.isna(v): job_data[k] = None
                        
                    new_jobs_to_insert.append(job_data)
                    
                # 3. BULK INSERT: Insert new jobs in chunks to save API calls
                if new_jobs_to_insert:
                    for i in range(0, len(new_jobs_to_insert), 100):
                        chunk = new_jobs_to_insert[i:i+100]
                        try:
                            supabase.table("jobs").insert(chunk).execute()
                            jobs_inserted += len(chunk)
                        except Exception as insert_e:
                            logger.error(f"Bulk insert failed: {insert_e}")
                            errors_count += len(chunk)
                            
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
