import os
import sqlite3
import uuid
import contextvars
from datetime import datetime

# Setup context var pointing to a test database in the scratch directory
TEST_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_jobs.db")
if os.path.exists(TEST_DB_PATH):
    os.remove(TEST_DB_PATH)

# Set the contextvar inside backend database
from backend.database import db_path_var, init_db, save_jobs, get_jobs

token = db_path_var.set(TEST_DB_PATH)
try:
    # Initialize the database
    init_db()
    print("Test database initialized at:", TEST_DB_PATH)

    # 1. Test saving a list of jobs
    test_jobs = [
        {
            "id": "job_1",
            "job_url": "https://careers.google.com/jobs/1",
            "title": "Software Engineer II - Cloud",
            "company": "Google",
            "location": "New York, NY",
            "source": "company_portal",
            "posted_date": "2026-06-13",
            "salary": "$150,000/yr",
            "description": "Looking for a cloud developer with python experience.",
            "remote_type": "hybrid",
            "visa_type": "h1b",
            "contract_type": "full-time",
            "score": 85,
            "reason": "Matches Python skills",
            "status": "identified",
            "emailed": False,
            "company_portal_url": "https://careers.google.com",
            "structured_data": {"role": "Engineer", "experience": "Mid"},
            "is_interested": False
        },
        {
            "id": "job_2",
            "job_url": "https://careers.microsoft.com/jobs/2",
            "title": "Senior Data Engineer",
            "company": "Microsoft",
            "location": "Remote",
            "source": "indeed",
            "posted_date": "2026-06-12",
            "salary": "$180,000/yr",
            "description": "SQL and python developer for big data analytics.",
            "remote_type": "remote",
            "visa_type": "unknown",
            "contract_type": "full-time",
            "score": 92,
            "reason": "Strong Python score",
            "status": "identified",
            "emailed": False,
            "company_portal_url": None,
            "structured_data": None,
            "is_interested": False
        }
    ]

    print("\n--- Test 1: Save Jobs ---")
    inserted = save_jobs(test_jobs)
    print(f"Inserted {inserted} new jobs (Expected: 2)")
    assert inserted == 2, "Test 1 failed"

    # Verify rows in DB
    conn = sqlite3.connect(TEST_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM jobs")
    count = cursor.fetchone()[0]
    print(f"Total jobs in database: {count} (Expected: 2)")
    assert count == 2, "Test 1 db count failed"
    conn.close()

    # 2. Test duplicate ignore
    print("\n--- Test 2: Duplicate Ignore ---")
    duplicate_jobs = [
        {
            "id": "job_1_dup",
            "job_url": "https://careers.google.com/jobs/1", # SAME URL
            "title": "Software Engineer II - Cloud",
            "company": "Google",
            "location": "New York, NY",
            "source": "company_portal"
        },
        {
            "id": "job_3",
            "job_url": "https://careers.netflix.com/jobs/3", # NEW URL
            "title": "Staff Python Engineer",
            "company": "Netflix",
            "location": "Los Gatos, CA",
            "source": "company_portal"
        }
    ]
    inserted_dup = save_jobs(duplicate_jobs)
    print(f"Inserted {inserted_dup} new jobs when duplicate present (Expected: 1)")
    assert inserted_dup == 1, "Test 2 failed"

    # Verify total rows is 3
    conn = sqlite3.connect(TEST_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM jobs")
    count = cursor.fetchone()[0]
    print(f"Total jobs in database now: {count} (Expected: 3)")
    assert count == 3, "Test 2 db count failed"
    conn.close()

    # 3. Test Search Endpoint Simulation
    print("\n--- Test 3: Search Simulation ---")
    # Simulate get_jobs or the API DB search
    def simulate_search(search_term, location=""):
        conn = sqlite3.connect(TEST_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query = "SELECT * FROM jobs WHERE 1=1"
        params = []
        
        query += " AND (title LIKE ? OR company LIKE ? OR description LIKE ?)"
        search_param = f"%{search_term}%"
        params.extend([search_param, search_param, search_param])
        
        if location:
            query += " AND location LIKE ?"
            loc_param = f"%{location}%"
            params.append(loc_param)
            
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    python_jobs = simulate_search("Python")
    print(f"Found {len(python_jobs)} python jobs (Expected: 3 - all mention Python or are Staff Python)")
    for j in python_jobs:
        print(f"  - {j['title']} at {j['company']}")
    assert len(python_jobs) == 3, "Test 3 python search failed"

    senior_jobs = simulate_search("Senior")
    print(f"Found {len(senior_jobs)} senior jobs (Expected: 1)")
    for j in senior_jobs:
        print(f"  - {j['title']} at {j['company']}")
    assert len(senior_jobs) == 1, "Test 3 senior search failed"

    ny_jobs = simulate_search("Engineer", "New York")
    print(f"Found {len(ny_jobs)} engineer jobs in NY (Expected: 1)")
    for j in ny_jobs:
        print(f"  - {j['title']} at {j['company']} (Location: {j['location']})")
    assert len(ny_jobs) == 1, "Test 3 NY search failed"

    print("\nAll tests completed successfully!")

finally:
    db_path_var.reset(token)
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
        print("\nCleaned up test database.")
