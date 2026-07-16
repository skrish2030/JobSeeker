import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from backend.database import is_sre_job

# Mock jobs
mock_jobs = [
    {"title": "Software Engineer", "score": 90, "created_at": "2026-06-20"},
    {"title": "Site Reliability Engineer", "score": 80, "created_at": "2026-06-19"},
    {"title": "Junior SRE", "score": 75, "created_at": "2026-06-18"},
    {"title": "Data Analyst", "score": 85, "created_at": "2026-06-17"},
]

print("Testing is_sre_job detection:")
for job in mock_jobs:
    print(f"Title: '{job['title']}' -> is_sre_job: {is_sre_job(job)}")

# Test search sorting simulation
print("\nSimulating sorting for active search:")
# We sort descending by SRE priority, then by score, then by created_at
sorted_search_jobs = sorted(
    mock_jobs, 
    key=lambda x: (1 if is_sre_job(x) else 0, int(x.get("score", 0)), x.get("created_at", "")), 
    reverse=True
)

for idx, job in enumerate(sorted_search_jobs):
    print(f"{idx+1}. {job['title']} (Score: {job['score']}, Date: {job['created_at']})")

# Assertions
assert is_sre_job(mock_jobs[1]) == True, "SRE job title not detected"
assert is_sre_job(mock_jobs[2]) == True, "SRE title with 'SRE' not detected"
assert is_sre_job(mock_jobs[0]) == False, "Non-SRE job false positive"

assert sorted_search_jobs[0]["title"] == "Site Reliability Engineer", "SRE job not sorted to top"
assert sorted_search_jobs[1]["title"] == "Junior SRE", "SRE job not sorted above non-SRE jobs"
assert sorted_search_jobs[2]["title"] == "Software Engineer", "Non-SRE jobs not sorted below SRE"
assert sorted_search_jobs[3]["title"] == "Data Analyst", "Non-SRE jobs not sorted by score"

print("\nAll sorting assertions passed successfully!")
