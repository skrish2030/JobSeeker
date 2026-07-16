import boto3
import sqlite3
import os

bucket_name = "jobseeker-data-bucket-v8ecp5q8"
s3_client = boto3.client("s3")

try:
    print(f"Listing all database files in S3 bucket '{bucket_name}' under prefix 'db/'...")
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix="db/")
    
    if 'Contents' not in response:
        print("No files found in the bucket under prefix 'db/'")
    else:
        print(f"{'S3 Key':<60} | {'Jobs Count':<10} | {'Size (Bytes)':<12}")
        print("-" * 90)
        for obj in response['Contents']:
            key = obj['Key']
            size = obj['Size']
            
            if not key.endswith(".db"):
                continue
                
            temp_filename = "temp_check.db"
            try:
                s3_client.download_file(bucket_name, key, temp_filename)
                
                conn = sqlite3.connect(temp_filename)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [r[0] for r in cursor.fetchall()]
                
                job_count = 0
                if "jobs" in tables:
                    cursor.execute("SELECT count(*) FROM jobs")
                    job_count = cursor.fetchone()[0]
                
                conn.close()
                print(f"{key:<60} | {job_count:<10} | {size:<12}")
            except Exception as inner_e:
                print(f"{key:<60} | Error: {inner_e}")
            finally:
                if os.path.exists(temp_filename):
                    os.remove(temp_filename)
                    
except Exception as e:
    print(f"Error listing S3 databases: {e}")
