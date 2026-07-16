import os
import requests
import json

def check_companies():
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

    # Fetch count of companies
    comp_url = f"{url}/rest/v1/companies?select=*"
    try:
        res = requests.get(comp_url, headers=headers, timeout=10)
        if res.status_code == 200:
            comps = res.json()
            print(f"[+] Total companies in database: {len(comps)}")
            for idx, c in enumerate(comps[:10], 1):
                print(f"  {idx}. {c.get('name')} | URL: {c.get('portal_url')}")
            if len(comps) > 10:
                print(f"  ... and {len(comps) - 10} more.")
        else:
            print(f"[-] Failed to fetch: HTTP {res.status_code} - {res.text}")
    except Exception as e:
        print(f"[-] Error: {e}")

if __name__ == "__main__":
    check_companies()
