import json
from pymongo import MongoClient, UpdateOne
from datetime import datetime

print("Connecting to MongoDB...")
client = MongoClient('mongodb://mongodb:27017/')
db = client.jobseeker

print("Loading JSON data...")
with open('/app/us_companies_job_portals.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Loaded {len(data)} companies from JSON. Preparing bulk insert...")

operations = []
for item in data:
    name = item.get("company_name", "").strip()
    url = item.get("career_portal_url", "").strip()
    if name:
        operations.append(
            UpdateOne(
                {"profile_id": "global", "company_name": name},
                {"$set": {"portal_url": url if url else None, "added_at": datetime.now().isoformat()}},
                upsert=True
            )
        )

if operations:
    print(f"Executing bulk write of {len(operations)} records. This may take a minute...")
    result = db.companies.bulk_write(operations, ordered=False)
    print(f"Successfully inserted/updated {result.upserted_count + result.modified_count} companies!")
else:
    print("No valid companies found to insert.")
