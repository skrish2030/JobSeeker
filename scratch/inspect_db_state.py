import sqlite3
import json
import os

db_path = "jobs.db"
if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name, portal_url FROM target_companies ORDER BY name ASC")
        companies = cursor.fetchall()
        print(f"Total companies in jobs.db: {len(companies)}")
        print("First 10 companies in jobs.db:")
        for c in companies[:10]:
            print(f"  {c[0]} -> {c[1]}")
        
        cursor.execute("SELECT count(*) FROM jobs")
        job_count = cursor.fetchone()[0]
        print(f"Total jobs in jobs.db: {job_count}")
        conn.close()
    except Exception as e:
        print(f"Error reading jobs.db: {e}")
else:
    print(f"jobs.db not found at {db_path}")

# Check user-specific databases
for f in os.listdir("."):
    if f.startswith("jobs_") and f.endswith(".db"):
        try:
            conn = sqlite3.connect(f)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [r[0] for r in cursor.fetchall()]
            
            tc_count = 0
            j_count = 0
            if "target_companies" in tables:
                cursor.execute("SELECT count(*) FROM target_companies")
                tc_count = cursor.fetchone()[0]
            if "jobs" in tables:
                cursor.execute("SELECT count(*) FROM jobs")
                j_count = cursor.fetchone()[0]
                
            print(f"User DB: {f} | target_companies: {tc_count} | jobs: {j_count} | Tables: {tables}")
            conn.close()
        except Exception as e:
            print(f"Error reading {f}: {e}")

# Let's search the JSON for some top recruiters/vendors
keywords = ["tek", "apex", "randstad", "robert half", "collabera", "kforce", "experis", "insight global", "adecco", "kelly", "aerotek", "judge group", "signature", "dexian", "vaco", "diversant", "eliassen", "beacon hill", "volt"]
print("\nSearching us_companies_job_portals.json for staffing keywords...")
if os.path.exists("us_companies_job_portals.json"):
    with open("us_companies_job_portals.json", "r", encoding="utf-8") as file:
        portals = json.load(file)
    print(f"Total portals in JSON: {len(portals)}")
    
    matches = []
    for p in portals:
        name = p.get("company_name", "")
        url = p.get("career_portal_url", "")
        category = p.get("category", "")
        
        # See if name contains any keyword
        name_lower = name.lower()
        matched_kw = None
        for kw in keywords:
            if kw in name_lower:
                matched_kw = kw
                break
        
        if matched_kw:
            matches.append((name, url, category, matched_kw))
            
    print(f"Found {len(matches)} matches matching keywords:")
    for m in matches[:50]:
        print(f"  {m[0]} -> {m[1]} (Category: {m[2]}, Keyword: {m[3]})")
else:
    print("us_companies_job_portals.json not found")
