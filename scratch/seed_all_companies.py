import os
import sqlite3
import json

db_files = ["jobs.db"]
for f in os.listdir("."):
    if f.startswith("jobs_") and f.endswith(".db"):
        db_files.append(f)

print(f"Target databases to seed all: {db_files}")

# Read the portals from JSON
json_path = "us_companies_job_portals.json"
if not os.path.exists(json_path):
    print(f"Error: {json_path} not found.")
    exit(1)

with open(json_path, "r", encoding="utf-8") as file:
    portals = json.load(file)

print(f"Loaded {len(portals)} portal definitions from JSON.")

# Prepare list of tuples
companies_data = []
seen = set()
for p in portals:
    name = p.get("company_name", "").strip()
    url = p.get("career_portal_url", "").strip()
    if not name:
        continue
    name_lower = name.lower()
    if name_lower not in seen:
        seen.add(name_lower)
        companies_data.append((name, url if url else None))

print(f"Prepared {len(companies_data)} unique companies to insert.")

# Seed databases in bulk
for db_file in db_files:
    if not os.path.exists(db_file):
        continue
        
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Ensure target_companies table exists and has portal_url
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
            # Check portal_url column
            cursor.execute("PRAGMA table_info(target_companies)")
            cols = [r[1] for r in cursor.fetchall()]
            if "portal_url" not in cols:
                cursor.execute("ALTER TABLE target_companies ADD COLUMN portal_url TEXT")
                
        # Insert all in a transaction
        cursor.execute("BEGIN TRANSACTION")
        cursor.executemany("""
        INSERT INTO target_companies (name, portal_url)
        VALUES (?, ?)
        ON CONFLICT(name) DO UPDATE SET portal_url = excluded.portal_url
        """, companies_data)
        conn.commit()
        
        cursor.execute("SELECT count(*) FROM target_companies")
        total_count = cursor.fetchone()[0]
        print(f"Seeded {db_file}. Total target companies: {total_count}")
        conn.close()
    except Exception as e:
        print(f"Error seeding database {db_file}: {e}")

print("Bulk seeding completed.")
