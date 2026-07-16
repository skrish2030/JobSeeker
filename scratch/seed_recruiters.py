import os
import sqlite3
import json

# Define the keywords for recruiters, staffing, vendors, and workforce solutions
recruiter_keywords = [
    "teksystem", "tek system", "apex system", "apex tech", "randstad", "robert half", 
    "collabera", "kforce", "experis", "insight global", "adecco", "kelly", 
    "aerotek", "judge group", "signature", "dexian", "vaco", "diversant", 
    "eliassen", "beacon hill", "volt", "staffing", "workforce", "personnel", 
    "manpower", "allegis", "actalent", "aston carter", "disys", "recruiting",
    "ciber", "modis", "yoh", "cross country", "maxim healthcare"
]

db_files = ["jobs.db"]
for f in os.listdir("."):
    if f.startswith("jobs_") and f.endswith(".db"):
        db_files.append(f)

print(f"Target databases to seed: {db_files}")

# Read the portals from JSON
json_path = "us_companies_job_portals.json"
if not os.path.exists(json_path):
    print(f"Error: {json_path} not found.")
    exit(1)

with open(json_path, "r", encoding="utf-8") as file:
    portals = json.load(file)

print(f"Loaded {len(portals)} portal definitions from JSON.")

# Find matching recruiters
matched_recruiters = []
seen_names = set()

for p in portals:
    name = p.get("company_name", "").strip()
    url = p.get("career_portal_url", "").strip()
    if not name or not url:
        continue
        
    name_lower = name.lower()
    is_match = False
    for kw in recruiter_keywords:
        if kw in name_lower:
            is_match = True
            break
            
    if is_match and name_lower not in seen_names:
        seen_names.add(name_lower)
        matched_recruiters.append((name, url))

# Add some prominent recruiters explicitly if they aren't matched or need precise URLs
explicit_recruiters = [
    ("TEKsystems", "https://www.teksystems.com/en/careers"),
    ("Apex Systems", "https://www.apexsystems.com/"),
    ("Randstad USA", "https://www.randstadusa.com/jobs/"),
    ("Robert Half", "https://www.roberthalf.com/us/en/jobs"),
    ("Collabera", "https://www.collabera.com/job-apply"),
    ("Kforce", "https://www.kforce.com/find-work/search-jobs/"),
    ("Experis", "https://www.experis.com/"),
    ("Insight Global", "https://insightglobal.com/jobs/"),
    ("Adecco USA", "https://www.adeccousa.com/"),
    ("Kelly Services", "https://www.kellyservices.us/"),
    ("Aerotek", "https://www.aerotek.com/en/careers"),
    ("Volt", "https://volt.com/"),
    ("Vaco", "https://boards.greenhouse.io/vaco"),
    ("Judge Group", "https://www.judge.com/"),
    ("Eliassen Group", "https://www.eliassen.com/"),
    ("Beacon Hill Staffing", "https://www.beaconhillstaffing.com/"),
    ("Dexian", "https://dexian.com/"),
]

for name, url in explicit_recruiters:
    name_lower = name.lower()
    if name_lower not in seen_names:
        seen_names.add(name_lower)
        matched_recruiters.append((name, url))

print(f"Found/Prepared {len(matched_recruiters)} recruiter/vendor portals to insert.")

# Seed databases
for db_file in db_files:
    if not os.path.exists(db_file):
        print(f"Skipping non-existent DB: {db_file}")
        continue
        
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Ensure the table target_companies exists and has portal_url
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='target_companies'")
        if not cursor.fetchone():
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS target_companies (
                name TEXT PRIMARY KEY,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                portal_url TEXT
            )
            """)
        else:
            # Check if portal_url column exists
            cursor.execute("PRAGMA table_info(target_companies)")
            cols = [r[1] for r in cursor.fetchall()]
            if "portal_url" not in cols:
                cursor.execute("ALTER TABLE target_companies ADD COLUMN portal_url TEXT")
        
        # Insert target companies
        inserted_count = 0
        for name, url in matched_recruiters:
            cursor.execute("""
            INSERT INTO target_companies (name, portal_url)
            VALUES (?, ?)
            ON CONFLICT(name) DO UPDATE SET portal_url = excluded.portal_url
            """, (name, url))
            if cursor.rowcount > 0:
                inserted_count += 1
                
        conn.commit()
        
        # Query total count
        cursor.execute("SELECT count(*) FROM target_companies")
        total_count = cursor.fetchone()[0]
        print(f"Successfully seeded {db_file}. Inserted/Updated recruiter count: {inserted_count}. Total company count: {total_count}")
        conn.close()
    except Exception as e:
        print(f"Error seeding database {db_file}: {e}")

print("Seeding process completed.")
