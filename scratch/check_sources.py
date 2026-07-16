import os
import requests
import json

def check_sources():
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

    # Fetch count by source_site
    # Grouping is not directly supported via Supabase REST API unless we use rpc.
    # But we can select all jobs and group them locally!
    jobs_url = f"{url}/rest/v1/jobs?select=source_site,scraped_at"
    try:
        res = requests.get(jobs_url, headers=headers, timeout=15)
        if res.status_code == 200:
            jobs = res.json()
            counts = {}
            for j in jobs:
                src = j.get("source_site", "unknown")
                counts[src] = counts.get(src, 0) + 1
            print("[+] Jobs by source site:")
            for src, cnt in counts.items():
                print(f"  {src}: {cnt} jobs")
        else:
            print(f"[-] Failed to fetch: HTTP {res.status_code}")
    except Exception as e:
        print(f"[-] Error: {e}")

if __name__ == "__main__":
    check_sources()
