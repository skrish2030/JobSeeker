import os
import requests
import json

def check_stats():
    url = "https://fhbuvrzvgqorgwxeoyyh.supabase.co"
    key = ""
    env_path = r"C:\Users\skris\OneDrive\Desktop\JobSeeker\.env"
    
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith("SUPABASE_SERVICE_KEY="):
                    key = line.split("=", 1)[1].strip()
                    
    if not key:
        print("[-] Supabase service key not found in .env!")
        return

    headers = {
        "Authorization": f"Bearer {key}",
        "apikey": key,
        "Content-Type": "application/json"
    }

    # 1. Fetch latest scrape logs
    logs_url = f"{url}/rest/v1/scrape_log?select=*&order=started_at.desc&limit=10"
    print("[*] Fetching latest scrape logs...")
    try:
        res = requests.get(logs_url, headers=headers, timeout=10)
        if res.status_code == 200:
            logs = res.json()
            print(f"[+] Latest Scraper Runs ({len(logs)}):")
            for log in logs:
                print(f"  Run ID: {log.get('run_id')}")
                print(f"    Started At: {log.get('started_at')}")
                print(f"    Finished At: {log.get('finished_at')}")
                print(f"    Jobs Inserted: {log.get('jobs_inserted')}")
                print(f"    Errors: {log.get('errors_count')}")
                print(f"    Notes: {log.get('notes')}")
                print("-" * 30)
        else:
            print(f"[-] Failed to fetch scrape logs: HTTP {res.status_code} - {res.text}")
    except Exception as e:
        print(f"[-] Error fetching logs: {e}")

    # 2. Fetch latest job dates
    jobs_url = f"{url}/rest/v1/jobs?select=title,company,location,scraped_at,posted_date&order=scraped_at.desc&limit=5"
    print("\n[*] Fetching latest jobs...")
    try:
        res = requests.get(jobs_url, headers=headers, timeout=10)
        if res.status_code == 200:
            jobs = res.json()
            print(f"[+] Latest Jobs Scraped ({len(jobs)}):")
            for job in jobs:
                print(f"  Title: {job.get('title')}")
                print(f"  Company: {job.get('company')}")
                print(f"  Scraped At: {job.get('scraped_at')}")
                print(f"  Posted Date: {job.get('posted_date')}")
                print("-" * 30)
        else:
            print(f"[-] Failed to fetch jobs: HTTP {res.status_code} - {res.text}")
    except Exception as e:
        print(f"[-] Error fetching jobs: {e}")

if __name__ == "__main__":
    check_stats()
