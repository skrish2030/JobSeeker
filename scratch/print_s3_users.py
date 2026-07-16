import boto3
import sqlite3
import os

bucket_name = "jobseeker-data-bucket-v8ecp5q8"
s3_client = boto3.client("s3")

try:
    print("Downloading master database db/jobs.db from S3...")
    s3_client.download_file(bucket_name, "db/jobs.db", "temp_master.db")
    
    conn = sqlite3.connect("temp_master.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cursor.fetchall()]
    print(f"Tables in master DB: {tables}")
    
    if "users" in tables:
        cursor.execute("SELECT id, username, email FROM users")
        print("\nRegistered Users:")
        for r in cursor.fetchall():
            print(f"  - User ID: {r['id']} | Username: {r['username']} | Email: {r['email']}")
            
    if "profiles" in tables:
        cursor.execute("SELECT id, user_id, name, db_path FROM profiles")
        print("\nProfiles:")
        for r in cursor.fetchall():
            print(f"  - Profile ID: {r['id']} | User ID: {r['user_id']} | Name: {r['name']} | DB Path: {r['db_path']}")
            
    conn.close()
    if os.path.exists("temp_master.db"):
        os.remove("temp_master.db")
except Exception as e:
    print(f"Error checking master database: {e}")
