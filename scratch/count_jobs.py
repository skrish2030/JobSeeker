import boto3
import sqlite3
import os

bucket_name = "jobseeker-data-bucket-v8ecp5q8"
db_name = "jobs_0bb4dd80-8f99-4be7-a268-368b588cb8c6_default.db"
s3_client = boto3.client("s3")

try:
    print(f"Downloading db/{db_name} from S3...")
    s3_client.download_file(bucket_name, f"db/{db_name}", "user_jobs.db")
    
    conn = sqlite3.connect("user_jobs.db")
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cursor.fetchall()]
    print(f"Tables present: {tables}")
    
    if "jobs" in tables:
        cursor.execute("SELECT count(*) FROM jobs")
        cnt = cursor.fetchone()[0]
        print(f"Number of jobs in 'jobs' table: {cnt}")
        
        if cnt > 0:
            cursor.execute("SELECT title, company, location, source, score FROM jobs LIMIT 5")
            print("\nFirst 5 jobs:")
            for r in cursor.fetchall():
                print(f"  - {r[0]} at {r[1]} ({r[2]}) | Source: {r[3]}, Score: {r[4]}")
                
    if "scrape_history" in tables:
        cursor.execute("SELECT * FROM scrape_history ORDER BY timestamp DESC LIMIT 5")
        print("\nLast 5 scrape history logs:")
        for r in cursor.fetchall():
            print(f"  - {r}")
            
    conn.close()
    
    if os.path.exists("user_jobs.db"):
        os.remove("user_jobs.db")
        
except Exception as e:
    print(f"Error checking user database: {e}")
