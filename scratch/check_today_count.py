import os
import requests
import json
from datetime import datetime

def count_today():
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

    # Fetch count of jobs scraped on 2026-07-16
    jobs_url = f"{url}/rest/v1/jobs?select=id,scraped_at&scraped_at=gte.2026-07-16T00:00:00"
    try:
        res = requests.get(jobs_url, headers=headers, timeout=10)
        if res.status_code == 200:
            jobs = res.json()
            print(f"[+] Total jobs scraped on 2026-07-16 in Supabase: {len(jobs)}")
            # Show the first few
            for idx, j in enumerate(jobs[:5], 1):
                print(f"  {idx}. ID: {j.get('id')} | Scraped At: {j.get('scraped_at')}")
        else:
            print(f"[-] Failed to fetch: HTTP {res.status_code} - {res.text}")
    except Exception as e:
        print(f"[-] Error: {e}")

if __name__ == "__main__":
    count_today()
