import os
import sys
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database import db_path_var, log_scrape_run, update_scrape_run, get_scrape_history

def test_status_flow():
    target_db = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "jobs_d98e5c12-179c-4f99-95a3-a89a95ff4964_default.db"))
    db_path_var.set(target_db)
    
    print("--- Simulating Scraper Startup ---")
    # Log starting state
    run_id = log_scrape_run(jobs_found=0, new_jobs=0, status="running")
    print(f"Logged active scrape run. Row ID: {run_id}")
    
    # Query status
    history = get_scrape_history(1)
    print(f"Latest status in history: '{history[0]['status']}' (ID: {history[0]['id']})")
    assert history[0]["status"] == "running", "Status should be 'running'!"
    
    print("\n--- Simulating Scraper Completion ---")
    # Update status to success
    update_scrape_run(run_id, jobs_found=12, new_jobs=3, status="success")
    print("Updated scrape run to success.")
    
    # Query status again
    history = get_scrape_history(1)
    print(f"Latest status in history: '{history[0]['status']}' (Jobs found: {history[0]['jobs_found']}, New: {history[0]['new_jobs']})")
    assert history[0]["status"] == "success", "Status should be 'success'!"
    assert history[0]["jobs_found"] == 12, "Jobs found should be 12!"
    
    print("\nSUCCESS: Scraper run status flow verification passed!")

if __name__ == "__main__":
    test_status_flow()
