import boto3
import sqlite3
import os

bucket_name = "jobseeker-data-bucket-v8ecp5q8"
s3_client = boto3.client("s3")

databases = [
    "jobs.db",
    "jobs_0bb4dd80-8f99-4be7-a268-368b588cb8c6_default.db"
]

for db in databases:
    try:
        print(f"\nProcessing {db}...")
        print(f"Downloading from S3...")
        s3_client.download_file(bucket_name, f"db/{db}", "temp_db.db")
        
        conn = sqlite3.connect("temp_db.db")
        cursor = conn.cursor()
        
        # Check current model
        cursor.execute("SELECT value FROM settings WHERE key = 'ai_model'")
        row = cursor.fetchone()
        current_model = row[0] if row else "None"
        print(f"Current model: {current_model}")
        
        # Update to gemini-2.0-flash
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('ai_model', 'gemini-2.0-flash')")
        conn.commit()
        
        cursor.execute("SELECT value FROM settings WHERE key = 'ai_model'")
        new_model = cursor.fetchone()[0]
        print(f"Updated model setting to: {new_model}")
        
        conn.close()
        
        print("Uploading updated database to S3...")
        s3_client.upload_file("temp_db.db", bucket_name, f"db/{db}")
        print(f"Successfully updated and uploaded {db}")
        
        if os.path.exists("temp_db.db"):
            os.remove("temp_db.db")
            
    except Exception as e:
        print(f"Error updating {db}: {e}")
        if os.path.exists("temp_db.db"):
            os.remove("temp_db.db")
