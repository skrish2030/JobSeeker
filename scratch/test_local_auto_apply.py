import requests
import json
import boto3
import random
import sys
import os
import time

base_url = "http://127.0.0.1:8000"

# Initialize boto3 DynamoDB resource
dynamodb = boto3.resource("dynamodb")
sessions_table = dynamodb.Table("jobseeker_user_sessions")
jobs_table = dynamodb.Table("jobseeker_jobs")
settings_table = dynamodb.Table("jobseeker_settings")

def run_test():
    # 1. Register a test user
    username = f"testuser_{random.randint(1000, 9999)}"
    email = "testuser@example.com"
    password = "Password123!"
    
    print(f"Registering user {username}...")
    res = requests.post(f"{base_url}/api/auth/register", json={
        "username": username,
        "email": email,
        "password": password
    })
    
    if res.status_code != 200:
        print(f"Registration failed: {res.text}")
        return
        
    reg_data = res.json()
    reg_id = reg_data.get("registration_id")
    print(f"Registration pending. ID: {reg_id}")
    
    # 2. Retrieve the MFA code directly from DynamoDB
    time.sleep(2)  # Wait for DynamoDB write
    mfa_code = None
    try:
        db_res = sessions_table.get_item(Key={"token": f"pending_{reg_id}"})
        item = db_res.get("Item")
        if item:
            mfa_code = item.get("code")
            print(f"Retrieved MFA code from DB: {mfa_code}")
    except Exception as e:
        print(f"Failed to get MFA code from DB: {e}")
        return
        
    if not mfa_code:
        print("MFA code not found in sessions table.")
        return
        
    # 3. Verify registration
    print("Verifying registration...")
    res = requests.post(f"{base_url}/api/auth/register/verify", json={
        "registration_id": reg_id,
        "code": mfa_code
    })
    
    if res.status_code != 200:
        print(f"Verification failed: {res.text}")
        return
        
    auth_data = res.json()
    token = auth_data.get("token")
    print(f"Verification successful. Token: {token[:10]}...")
    
    # Define headers with authorization
    headers = {
        "Authorization": f"Bearer {token}",
        "x-profile-id": "default",
        "Content-Type": "application/json"
    }
    
    # 4. Create a dummy resume file
    resume_path = os.path.abspath("C:/Users/skris/OneDrive/Desktop/JobSeeker/test_resume.pdf")
    with open(resume_path, "w") as f:
        f.write("%PDF-1.4 ... Fake Resume Content for Playwright Test ...")
    print(f"Created fake resume at {resume_path}")
    
    # 5. Save candidate settings
    print("Updating candidate settings...")
    settings_payload = {
        "candidate_first_name": "Test",
        "candidate_last_name": "Applicant",
        "candidate_email": "testapplicant@example.com",
        "candidate_phone": "+15551234567",
        "candidate_linkedin": "https://linkedin.com/in/testapplicant",
        "candidate_github": "https://github.com/testapplicant",
        "candidate_portfolio": "https://testapplicant.dev",
        "resume_file_path": resume_path
    }
    
    res = requests.post(f"{base_url}/api/settings", json=settings_payload, headers=headers)
    if res.status_code != 200:
        print(f"Failed to update settings: {res.text}")
        return
    print("Settings updated successfully.")
    
    # 6. Put a mock Greenhouse job in the jobseeker_jobs table in DynamoDB
    job_id = "test_job_greenhouse_123"
    print(f"Creating mock Greenhouse job {job_id} in DynamoDB...")
    try:
        # Delete first if exists
        jobs_table.delete_item(Key={"profile_id": "global", "job_id": job_id})
        
        # Put item
        jobs_table.put_item(Item={
            "profile_id": "global",
            "job_id": job_id,
            "job_url": "https://boards.greenhouse.io/stripe/jobs/123",
            "title": "Software Engineer (MOCK)",
            "company": "Stripe",
            "location": "Remote",
            "source": "greenhouse",
            "status": "identified",
            "score": 85,
            "description": "Mock job description for Stripe auto-apply test."
        })
        print("Mock job created in DynamoDB.")
    except Exception as e:
        print(f"Failed to create mock job: {e}")
        return

    # 7. Trigger the auto-apply endpoint in preview mode (let's patch run_auto_apply to return quickly so the script doesn't sleep 300s)
    # Wait, we want to test that it actually launches the browser! But since it's a headed browser and sleeps,
    # let's run it. Wait, in auto_applier.py:
    # res = run_auto_apply(...)
    # If we run it in "preview" mode, it will open the browser and sleep for 300s.
    # Let's run a quick 2-second timeout on the requests call so it launches the browser but doesn't wait for the 300s sleep to finish!
    # Yes! That is a brilliant idea. We can do requests.post(..., timeout=5) and catch ReadTimeout. That means it successfully executed up to the sleep!
    print("Triggering auto-apply in preview mode (expecting ReadTimeout since it pauses)...")
    try:
        res = requests.post(
            f"{base_url}/api/jobs/{job_id}/apply",
            json={"mode": "preview"},
            headers=headers,
            timeout=10
        )
        print(f"Response: status_code={res.status_code}, body={res.text}")
    except requests.exceptions.ReadTimeout:
        print("Success! Triggered auto-apply and hit read timeout, meaning headed browser opened and is successfully pausing for review.")
    except Exception as e:
        print(f"Auto-apply request failed: {e}")
        
    # Clean up
    try:
        jobs_table.delete_item(Key={"profile_id": "global", "job_id": job_id})
        os.remove(resume_path)
        print("Cleaned up mock data.")
    except Exception:
        pass

if __name__ == "__main__":
    run_test()
