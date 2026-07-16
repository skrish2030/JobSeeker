import os
import sys
import time
import random
import logging
import hashlib
from datetime import datetime

# Add project root to path to resolve backend/scraper imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import create_client, Client
from dotenv import load_dotenv

# Try importing the company scrapers from backend
try:
    from backend.ats_scraper import scrape_single_company
except ImportError:
    # Fallback to absolute sys.path inclusion
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.append(project_root)
    from backend.ats_scraper import scrape_single_company

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "heavy_scheduler.log"), encoding="utf-8")
    ]
)
logger = logging.getLogger("heavy_scheduler")

# Local Block Logger File
BLOCKED_LOG_FILE = os.path.join(os.path.dirname(__file__), "blocked_sources.log")

def log_blocked_site(company_name, url, platform, error_msg):
    """Logs blocked or failed websites to a local file for manual review."""
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] COMPANY: {company_name} | URL: {url} | PLATFORM: {platform} | ERROR: {error_msg}\n"
    try:
        with open(BLOCKED_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
        logger.warning(f"⚠️ Source Blocked: {company_name} ({url}) - logged to blocked_sources.log")
    except Exception as e:
        logger.error(f"Failed to write to local blocked log: {e}")

def get_supabase_client() -> Client:
    # Search root and current folders for .env
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend-next", ".env.local"))
    
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not key:
        # Final fallback check in standard env variables
        url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
        key = os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")
        
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in environment variables or .env file.")
    return create_client(url, key)

def run_jobspy_cycle(supabase: Client):
    """Runs a single optimized aggregator scrape cycle for Indeed/LinkedIn."""
    logger.info("Starting JobSpy Aggregator scrape cycle...")
    try:
        from scraper.main import run_scraper
        run_scraper()
        logger.info("JobSpy cycle completed successfully.")
    except Exception as e:
        logger.error(f"JobSpy scrape cycle failed: {e}")

def run_corporate_ats_cycle(supabase: Client, batch_size=10):
    """
    Fetches target companies from Supabase, chunks them, and scrapes them in small batches
    with time delays to prevent IP bans and rate-limiting.
    """
    logger.info("Starting Corporate ATS scrape cycle...")
    try:
        # 1. Fetch companies
        comp_res = supabase.table("companies").select("*").execute()
        companies = comp_res.data or []
        if not companies:
            logger.info("No corporate companies found in target database list.")
            return
            
        logger.info(f"Retrieved {len(companies)} corporate companies to scrape.")
        
        # 2. Fetch search keywords from settings
        # Default keywords to target if settings don't exist
        search_terms = "Software Engineer, Data Engineer, Site Reliability Engineer"
        try:
            settings_res = supabase.table("settings").select("search_terms").eq("id", "global").execute()
            if settings_res.data:
                search_terms = settings_res.data[0].get("search_terms") or search_terms
        except Exception:
            pass
            
        # Shuffle companies to randomize requests
        random.shuffle(companies)
        
        # 3. Process in small staggered batches
        for i in range(0, len(companies), batch_size):
            batch = companies[i:i+batch_size]
            logger.info(f"Processing batch {i//batch_size + 1} ({len(batch)} companies)...")
            
            for comp in batch:
                name = comp.get("name")
                url = comp.get("portal_url")
                
                logger.info(f"Direct Scraping: {name} (URL: {url})")
                try:
                    # Run the single scraper
                    jobs = scrape_single_company(comp, search_terms)
                    
                    if jobs:
                        # Upload found jobs
                        logger.info(f"Found {len(jobs)} jobs for {name}. Ingesting to Supabase...")
                        
                        # Prepare payload for Supabase jobs table
                        ingest_jobs = []
                        for job in jobs:
                            # Avoid duplicate check by hashing fields
                            hash_str = f"{job['title']}-{job['company']}-{job['location']}".lower()
                            job_hash = hashlib.md5(hash_str.encode('utf-8')).hexdigest()
                            
                            ingest_jobs.append({
                                "job_hash": job_hash,
                                "title": job["title"],
                                "company": job["company"],
                                "location": job["location"],
                                "source_site": job.get("source", "company_portal"),
                                "job_url": job["job_url"],
                                "description": job.get("description", ""),
                                "posted_date": job.get("posted_date", datetime.today().strftime('%Y-%m-%d'))
                            })
                            
                        # Upsert batch (ignoring existing hashes)
                        for job_data in ingest_jobs:
                            try:
                                supabase.table("jobs").upsert(job_data, on_conflict="job_hash").execute()
                            except Exception as upsert_e:
                                # If blocked/rejected by database constraints
                                if "403" in str(upsert_e) or "429" in str(upsert_e):
                                    log_blocked_site(name, url, "database_upsert", str(upsert_e))
                                    
                    # Throttling delay between company portals to keep scraper stealthy
                    sleep_time = random.uniform(8.0, 15.0)
                    time.sleep(sleep_time)
                    
                except Exception as comp_e:
                    err_msg = str(comp_e)
                    platform = "unknown"
                    if url:
                        if "greenhouse" in url.lower(): platform = "greenhouse"
                        elif "lever" in url.lower(): platform = "lever"
                        elif "ashby" in url.lower(): platform = "ashby"
                        elif "workday" in url.lower(): platform = "workday"
                        
                    # Check for rate limiting / blocking indicators
                    if any(indicator in err_msg.lower() for indicator in ["403", "429", "forbidden", "captcha", "blocked", "denied", "timeout"]):
                        log_blocked_site(name, url, platform, err_msg)
                    else:
                        logger.error(f"Error scraping company {name}: {err_msg}")
                        
            # Intermediate delay between batches to cool down IP
            batch_cooldown = random.uniform(60.0, 120.0)
            logger.info(f"Finished batch. Cooling down for {batch_cooldown:.1f} seconds...")
            time.sleep(batch_cooldown)
            
    except Exception as e:
        logger.error(f"Corporate ATS scrape cycle failed: {e}")

def main():
    logger.info("=" * 50)
    logger.info("JOBSEEKER 24/7 HEAVY SCALING LOCAL SCHEDULER")
    logger.info("=" * 50)
    logger.info(f"Logging active. Blocked sites will append to: {BLOCKED_LOG_FILE}")
    
    try:
        supabase = get_supabase_client()
        logger.info("[+] Supabase client initialized successfully.")
    except Exception as e:
        logger.critical(f"[-] Database connection failed: {e}")
        return

    # Configuration intervals (in seconds)
    JOBSPY_INTERVAL = 3600  # Run JobSpy aggregators every 1 hour
    ATS_BATCH_SIZE = 10     # Process 10 corporate portals at a time
    ATS_INTERVAL = 1800     # Run ATS batch cycle every 30 minutes
    
    last_jobspy_run = 0
    last_ats_run = 0

    logger.info("[+] Starting infinite scheduler loop. Press Ctrl+C to terminate.")
    
    while True:
        try:
            now = time.time()
            
            # 1. JobSpy Aggregators (Indeed / LinkedIn) Scheduler
            if now - last_jobspy_run >= JOBSPY_INTERVAL:
                logger.info("Triggering JobSpy runner...")
                run_jobspy_cycle(supabase)
                last_jobspy_run = time.time()
                
            # 2. Corporate ATS Portals (Greenhouse, Lever, Ashby, Workday) Scheduler
            if now - last_ats_run >= ATS_INTERVAL:
                logger.info("Triggering ATS corporate batch runner...")
                run_corporate_ats_cycle(supabase, batch_size=ATS_BATCH_SIZE)
                last_ats_run = time.time()
                
            # Idle sleep to prevent high CPU cycles
            time.sleep(10)
            
        except KeyboardInterrupt:
            logger.info("[-] Shutdown signal received. Exiting local scheduler.")
            break
        except Exception as loop_e:
            logger.error(f"Unexpected error in scheduler loop: {loop_e}")
            time.sleep(30)

if __name__ == "__main__":
    main()
