import boto3
import sqlite3
import os

bucket_name = "jobseeker-data-bucket-v8ecp5q8"
s3_client = boto3.client("s3")

try:
    print(f"Downloading db/jobs.db from S3 bucket {bucket_name}...")
    s3_client.download_file(bucket_name, "db/jobs.db", "scratch_jobs.db")
    
    conn = sqlite3.connect("scratch_jobs.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings")
    rows = cursor.fetchall()
    conn.close()
    
    settings = {row['key']: row['value'] for row in rows}
    print("\nSettings in S3 master database:")
    for k, v in settings.items():
        if 'key' in k or 'pass' in k or 'sender' in k or 'recipient' in k:
            print(f"  - {k}: {'********' if v else 'empty'}")
        else:
            print(f"  - {k}: {v}")
            
    # Clean up
    if os.path.exists("scratch_jobs.db"):
        os.remove("scratch_jobs.db")
        
except Exception as e:
    print(f"Error checking S3 master db: {e}")
