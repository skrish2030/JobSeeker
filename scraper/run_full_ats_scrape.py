import os
import sys
import time
import hashlib
from datetime import datetime

# Add project root to path to resolve backend/scraper imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import create_client, Client

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Try importing the company scrapers from backend
try:
    from backend.ats_scraper import scrape_single_company
except ImportError:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.append(project_root)
    from backend.ats_scraper import scrape_single_company

# Local Block Logger File
BLOCKED_LOG_FILE = os.path.join(os.path.dirname(__file__), "blocked_sources.log")

def log_blocked_site(company_name, url, platform, error_msg):
    """Logs blocked or failed websites to a local file for manual review."""
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] COMPANY: {company_name} | URL: {url} | PLATFORM: {platform} | ERROR: {error_msg}\n"
    try:
        with open(BLOCKED_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        print(f"    [!] Failed to write to local blocked log: {e}")

def load_env_manually(filepath):
    """Fallback manual parser for .env files when python-dotenv is not installed."""
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip().strip('"').strip("'")
        except Exception as e:
            print(f"    [!] Failed to read {filepath} manually: {e}")

def get_supabase_client() -> Client:
    # Attempt manual parse fallback
    load_env_manually(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    load_env_manually(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend-next", ".env.local"))
    
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not key:
        url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
        key = os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")
        
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in environment variables or .env file.")
    return create_client(url, key)

def run_full_scrape():
    print("=" * 60)
    print("   JOBSEEKER DIRECT COMPANY PORTAL SCRAPER (FULL RUN)")
    print("=" * 60)
    
    try:
        supabase = get_supabase_client()
        print("[+] Supabase connection successful.")
    except Exception as e:
        print(f"[-] Database connection failed: {e}")
        return

    # 1. Fetch companies
    try:
        comp_res = supabase.table("companies").select("*").execute()
        companies = comp_res.data or []
    except Exception as e:
        print(f"[-] Failed to fetch companies table: {e}")
        return
        
    if not companies:
        print("[-] No companies found in the 'companies' database table.")
        return

    total_companies = len(companies)
    print(f"[+] Found {total_companies} companies to scrape.")
    
    # 2. Skip title filtering to retrieve ALL job postings from corporate portals
    search_terms = ""
    print("[+] Title filtering disabled: Scraping ALL open roles.")
    print("-" * 60)

    success_count = 0
    blocked_count = 0
    total_jobs_inserted = 0
    
    # Loop sequentially through all companies
    for index, comp in enumerate(companies, 1):
        name = comp.get("name")
        url = comp.get("portal_url")
        print(f"[{index}/{total_companies}] Scraping '{name}'...")
        if url:
            print(f"    Portal URL: {url}")
        else:
            print(f"    Portal URL: None (Guessing slug based on name)")

        platform = "unknown"
        if url:
            if "greenhouse" in url.lower(): platform = "greenhouse"
            elif "lever" in url.lower(): platform = "lever"
            elif "ashby" in url.lower(): platform = "ashby"
            elif "workday" in url.lower(): platform = "workday"

        try:
            # Execute scraper
            jobs = scrape_single_company(comp, search_terms)
            
            if jobs is not None:
                success_count += 1
                jobs_count = len(jobs)
                print(f"    --> STATUS: SUCCESS (Found {jobs_count} matching jobs)")
                
                if jobs_count > 0:
                    print("    --> Uploading jobs to Supabase...")
                    ingest_jobs = []
                    for job in jobs:
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
                    
                    inserted_this_batch = 0
                    for job_data in ingest_jobs:
                        try:
                            supabase.table("jobs").upsert(job_data, on_conflict="job_hash").execute()
                            inserted_this_batch += 1
                            total_jobs_inserted += 1
                        except Exception as upsert_e:
                            if "403" in str(upsert_e) or "429" in str(upsert_e):
                                log_blocked_site(name, url, "database_upsert", str(upsert_e))
                    print(f"    --> Database Ingested: {inserted_this_batch} jobs saved.")
            else:
                # If returned None (which some blocked functions do)
                blocked_count += 1
                print(f"    --> STATUS: BLOCKED/EMPTY (No jobs returned)")
                log_blocked_site(name, url, platform, "Empty return / possible bot block")
                
        except Exception as comp_e:
            err_msg = str(comp_e)
            if any(indicator in err_msg.lower() for indicator in ["403", "429", "forbidden", "captcha", "blocked", "denied", "timeout"]):
                blocked_count += 1
                print(f"    --> STATUS: BLOCKED ({err_msg})")
                log_blocked_site(name, url, platform, err_msg)
            else:
                print(f"    --> STATUS: ERROR ({err_msg})")
                
        # 3. Micro sleep delay to not flood servers
        time.sleep(3.0)
        print("-" * 40)

    print("\n" + "=" * 60)
    print("   SCRAPE CYCLE RUN SUMMARY")
    print("=" * 60)
    print(f"Total Companies Checked: {total_companies}")
    print(f"Successful Portals Scraped: {success_count}")
    print(f"Blocked or Empty Portals: {blocked_count}")
    print(f"Total Jobs Upserted to Database: {total_jobs_inserted}")
    print(f"Blocked details appended to: {BLOCKED_LOG_FILE}")
    print("=" * 60)

if __name__ == "__main__":
    run_full_scrape()
