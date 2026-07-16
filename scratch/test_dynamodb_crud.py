import sys
import os
import uuid
from datetime import datetime

# Add the project root to python path so backend can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import (
    active_user_id_var,
    active_profile_id_var,
    create_user,
    get_user_by_username,
    get_user_by_id,
    add_profile,
    get_profiles,
    delete_profile,
    get_all_settings,
    update_settings,
    add_target_company,
    get_target_companies,
    delete_target_company,
    save_jobs,
    get_jobs,
    get_job_by_id,
    delete_interested_job,
    dynamodb,
    DYNAMODB_USERS_TABLE,
    DYNAMODB_JOBS_TABLE,
    DYNAMODB_SETTINGS_TABLE
)

def run_tests():
    print("==================================================")
    print("     JobSeeker DynamoDB CRUD Integration Test")
    print("==================================================")

    # Initialize unique test variables
    test_user_id = f"test-user-{uuid.uuid4().hex[:8]}"
    test_username = f"testuser_{uuid.uuid4().hex[:8]}"
    test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    test_pwd_hash = "salt:hashedpassword123"
    test_job_url = f"https://example.com/jobs/{uuid.uuid4().hex}"
    
    print(f"\n[INFO] Test Username: {test_username}")
    print(f"[INFO] Test User ID: {test_user_id}")
    print(f"[INFO] Test Email: {test_email}")

    # Set context variables for context-scoped database queries
    u_token = active_user_id_var.set(test_user_id)
    p_token = active_profile_id_var.set("default")
    
    try:
        # 1. Test User Creation
        print("\n[STEP 1] Creating test user in DynamoDB...")
        success = create_user(test_user_id, test_username, test_email, test_pwd_hash)
        if not success:
            print("[FAIL] Failed to create user.")
            return False
        print("[PASS] User created successfully.")

        # 2. Test User Retrieval
        print("\n[STEP 2] Fetching user details...")
        user_by_name = get_user_by_username(test_username)
        if not user_by_name or user_by_name.get("id") != test_user_id:
            print(f"[FAIL] get_user_by_username failed. Got: {user_by_name}")
            return False
        print("[PASS] get_user_by_username validated.")

        user_by_id = get_user_by_id(test_user_id)
        if not user_by_id or user_by_id.get("username") != test_username:
            print(f"[FAIL] get_user_by_id failed. Got: {user_by_id}")
            return False
        print("[PASS] get_user_by_id validated.")

        # 3. Test Profile Creation & Retrieval
        print("\n[STEP 3] Adding and listing user profile...")
        add_profile("default", test_user_id, "Test Profile", "#ff5722", "")
        profiles = get_profiles(test_user_id)
        if not profiles or not any(p["id"] == "default" for p in profiles):
            print(f"[FAIL] get_profiles failed. Got: {profiles}")
            return False
        print("[PASS] Profile created and verified.")

        # 4. Test Settings Retrieval & Updates
        print("\n[STEP 4] Testing profile settings...")
        settings = get_all_settings()
        print(f"Default search terms: {settings.get('search_terms')}")
        
        new_terms = "Python, Golang, AWS Developer"
        update_settings({"search_terms": new_terms})
        
        updated_settings = get_all_settings()
        if updated_settings.get("search_terms") != new_terms:
            print(f"[FAIL] Settings update failed. Got: {updated_settings}")
            return False
        print("[PASS] Settings update verified successfully.")

        # 5. Test Target Companies CRUD
        print("\n[STEP 5] Testing target companies CRUD...")
        add_target_company("Unique Test Company", "https://uniquetest.com/careers")
        companies = get_target_companies()
        matched = [c for c in companies if c["name"] == "Unique Test Company"]
        if not matched or matched[0]["portal_url"] != "https://uniquetest.com/careers":
            print(f"[FAIL] add_target_company failed. Got: {companies}")
            return False
        print("[PASS] Target company added successfully.")

        delete_target_company("Unique Test Company")
        companies_after = get_target_companies()
        if any(c["name"] == "Unique Test Company" for c in companies_after):
            print("[FAIL] delete_target_company failed.")
            return False
        print("[PASS] Target company deleted successfully.")

        # 6. Test Job Saving & Querying (Global scope)
        print("\n[STEP 6] Testing job save and querying...")
        test_job = {
            "title": "Staff Engineer",
            "company": "Amazing Scale Company",
            "location": "Remote, USA",
            "job_url": test_job_url,
            "source": "manual",
            "posted_date": "2026-06-20",
            "salary": "$200,000/yr",
            "description": "Looking for a python AWS system engineer.",
            "remote_type": "remote",
            "visa_type": "unknown",
            "contract_type": "full-time",
            "score": 95,
            "reason": "Highly qualified",
            "status": "identified",
            "is_interested": True
        }
        
        new_jobs = save_jobs([test_job])
        print(f"Saved {new_jobs} new jobs to the global database.")
        
        # Verify job is queryable
        all_jobs = get_jobs()
        saved_job_matches = [j for j in all_jobs if j["job_url"] == test_job_url]
        if not saved_job_matches:
            print(f"[FAIL] Job not found in global search.")
            return False
        
        saved_job = saved_job_matches[0]
        print(f"[PASS] Job saved and retrieved from DB. Title: {saved_job['title']}, Score: {saved_job['score']}")
        
        # Clean up test jobs
        print("\n[STEP 7] Cleaning up test jobs...")
        delete_interested_job(saved_job["id"])
        job_check = get_job_by_id(saved_job["id"])
        if job_check:
            print(f"[FAIL] Job cleanup failed, job still exists: {job_check}")
            return False
        print("[PASS] Job cleaned up successfully.")

        # 8. Clean up user
        print("\n[STEP 8] Cleaning up test user...")
        delete_profile("default", test_user_id)
        
        users_table = dynamodb.Table(DYNAMODB_USERS_TABLE)
        users_table.delete_item(Key={"username": test_username})
        
        settings_table = dynamodb.Table(DYNAMODB_SETTINGS_TABLE)
        settings_table.delete_item(Key={"profile_id": f"{test_user_id}_default"})
        
        print("[PASS] Test user, profile, and settings cleaned up.")
        
        print("\n==================================================")
        print("  ALL DYNAMODB CRUD TESTS COMPLETED SUCCESSFULLY! ")
        print("==================================================")
        return True

    except Exception as e:
        print(f"\n[FAIL] Test crashed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        active_user_id_var.reset(u_token)
        active_profile_id_var.reset(p_token)

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
