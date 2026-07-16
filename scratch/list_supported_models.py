import boto3
import sqlite3
import requests
import os

bucket_name = "jobseeker-data-bucket-v8ecp5q8"
s3_client = boto3.client("s3")

try:
    print(f"Downloading db/jobs.db from S3...")
    s3_client.download_file(bucket_name, "db/jobs.db", "scratch_jobs.db")
    
    conn = sqlite3.connect("scratch_jobs.db")
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'ai_api_key'")
    row = cursor.fetchone()
    conn.close()
    
    api_key = row[0] if row else ""
    
    if os.path.exists("scratch_jobs.db"):
        os.remove("scratch_jobs.db")
        
    if not api_key:
        print("No Gemini API key found in the database settings.")
    else:
        print(f"Gemini API key retrieved (length: {len(api_key)})")
        
        # Query list models
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        res = requests.get(url)
        if res.status_code == 200:
            models = res.json().get("models", [])
            print("\nAvailable models in your Google AI Studio account:")
            for m in models:
                name = m.get("name", "").replace("models/", "")
                display_name = m.get("displayName", "")
                supported_methods = m.get("supportedGenerationMethods", [])
                if "generateContent" in supported_methods:
                    print(f"  - {name} ({display_name})")
        else:
            print(f"\nFailed to query Gemini API (status {res.status_code}): {res.text}")
            
except Exception as e:
    print(f"Error: {e}")
