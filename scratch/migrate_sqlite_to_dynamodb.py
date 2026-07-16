import sqlite3
import boto3
import json
from datetime import datetime

sqlite_db_path = "C:/Users/skris/OneDrive/Desktop/JobSeeker/jobs_ee663882-f722-4f10-a39c-159fe7dc8509_default.db"
user_id = "e2f9bcc0-8170-4742-a1ea-4f65636bb61b"
profile_id = "default"
user_profile_key = f"{user_id}_{profile_id}"

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

print(f"Connecting to SQLite database: {sqlite_db_path}")
conn = sqlite3.connect(sqlite_db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 1. Migrate Jobs
print("Migrating jobs to jobseeker_jobs...")
cursor.execute("SELECT * FROM jobs")
rows = cursor.fetchall()
jobs_table = dynamodb.Table("jobseeker_jobs")

with jobs_table.batch_writer() as batch:
    for row in rows:
        job = dict(row)
        # Rename id to job_id if needed
        job_id = job.get("id")
        
        # Prepare item for DynamoDB
        item = {
            "profile_id": "global",
            "job_id": job_id,
            "job_url": job.get("job_url") or "",
            "title": job.get("title") or "Untitled Role",
            "company": job.get("company") or "Unknown Company",
            "location": job.get("location") or "Remote",
            "source": job.get("source") or "job_board",
            "posted_date": job.get("posted_date") or "",
            "salary": job.get("salary") or "Not disclosed",
            "description": job.get("description") or "",
            "remote_type": job.get("remote_type") or "unknown",
            "visa_type": job.get("visa_type") or "unknown",
            "contract_type": job.get("contract_type") or "unknown",
            "score": int(job.get("score") or 0),
            "reason": job.get("reason") or "",
            "status": job.get("status") or "identified",
            "emailed": bool(job.get("emailed", False)),
            "company_portal_url": job.get("company_portal_url"),
            "structured_data": job.get("structured_data") or "",
            "is_interested": bool(job.get("is_interested", False)),
            "created_at": job.get("created_at") or datetime.now().isoformat()
        }
        batch.put_item(Item=item)
print(f"Successfully migrated {len(rows)} jobs!")

# 2. Migrate Target Companies
print("Migrating target companies to jobseeker_target_companies...")
cursor.execute("SELECT * FROM target_companies")
rows = cursor.fetchall()
companies_table = dynamodb.Table("jobseeker_target_companies")

with companies_table.batch_writer() as batch:
    for row in rows:
        comp = dict(row)
        name = comp.get("name")
        portal_url = comp.get("portal_url")
        # Put under user_profile_key
        batch.put_item(Item={
            "profile_id": user_profile_key,
            "company_name": name.strip(),
            "portal_url": portal_url.strip() if portal_url else None,
            "added_at": comp.get("added_at") or datetime.now().isoformat()
        })
        # Put under global as well
        batch.put_item(Item={
            "profile_id": "global",
            "company_name": name.strip(),
            "portal_url": portal_url.strip() if portal_url else None,
            "added_at": comp.get("added_at") or datetime.now().isoformat()
        })
print(f"Successfully migrated {len(rows)} target companies!")

# 3. Migrate Settings
print("Migrating settings to jobseeker_settings...")
cursor.execute("SELECT * FROM settings")
rows = cursor.fetchall()
settings_table = dynamodb.Table("jobseeker_settings")

if rows:
    settings_dict = dict(rows[0])
    # Put under user_profile_key
    item = {"profile_id": user_profile_key}
    for k, v in settings_dict.items():
        if k != "profile_id" and v is not None:
            # Check if boolean or int, convert to string as settings fields are strings
            if isinstance(v, bool):
                item[k] = "true" if v else "false"
            else:
                item[k] = str(v)
    
    settings_table.put_item(Item=item)
    print("Successfully migrated settings!")
else:
    print("No settings found in SQLite to migrate.")

conn.close()
print("Migration completed!")
