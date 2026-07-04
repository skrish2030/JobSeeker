import os
import logging
import hashlib
from datetime import datetime
from supabase import create_client, Client
from jobspy import scrape_jobs
import google.generativeai as genai
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gh_scraper")

def get_supabase() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
    return create_client(url, key)

def run_scraper():
    supabase = get_supabase()
    
    # 1. Fetch settings
    settings_res = supabase.table("settings").select("*").eq("id", "global").execute()
    settings = settings_res.data[0] if settings_res.data else {}
    
    ai_provider = settings.get("ai_provider", "Gemini")
    ai_model = settings.get("ai_model", "gemini-1.5-flash")
    ai_api_key = os.environ.get("GOOGLE_API_KEY")
    
    # Target keywords and locations can be configured here or in settings.
    # For a public board, we can hardcode some defaults or read from a 'keywords' table.
    # Let's use generic defaults.
    keywords = ["Software Engineer", "Frontend Developer", "Backend Developer"]
    location = "Remote"
    
    # Create log entry
    log_res = supabase.table("scrape_log").insert({
        "run_id": os.environ.get("GITHUB_RUN_ID", "local"),
        "notes": f"Scraping for {len(keywords)} keywords in {location}"
    }).execute()
    log_id = log_res.data[0]["id"]
    
    jobs_inserted = 0
    errors_count = 0
    
    if ai_api_key:
        genai.configure(api_key=ai_api_key)
        
    for kw in keywords:
        logger.info(f"Scraping '{kw}' in '{location}'...")
        try:
            df = scrape_jobs(
                site_name=["indeed", "linkedin", "glassdoor"],
                search_term=kw,
                location=location,
                results_wanted=30,
                hours_old=24,
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
                
                # AI Classification (Optional)
                score = 50
                if ai_api_key:
                    try:
                        model = genai.GenerativeModel(ai_model)
                        prompt = f"Evaluate this job for a mid-level software engineer. Return ONLY JSON with a 'score' 0-100.\n\nTitle: {title}\nCompany: {company}\nDescription: {desc[:2000]}"
                        resp = model.generate_content(prompt)
                        # Basic JSON extraction
                        text = resp.text.strip()
                        if text.startswith("```json"):
                            text = text[7:-3].strip()
                        ai_data = json.loads(text)
                        score = ai_data.get("score", 50)
                    except Exception as ai_e:
                        logger.error(f"AI classification failed for {title}: {ai_e}")
                
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
                    "score": score
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
            logger.error(f"Scraper failed for {kw}: {e}")
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
