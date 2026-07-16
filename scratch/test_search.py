import os
import sys

# Ensure backend folder is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database import db_path_var, get_jobs, get_all_settings

def run_tests():
    # Set the target database path
    target_db = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "jobs_d98e5c12-179c-4f99-95a3-a89a95ff4964_default.db"))
    print(f"Target DB: {target_db}")
    print(f"File exists: {os.path.exists(target_db)}")
    
    db_path_var.set(target_db)
    
    print("\n--- Testing get_jobs filters ---")
    # Search for 'java'
    java_jobs = get_jobs({"search": "java"})
    print(f"Found {len(java_jobs)} jobs matching 'java'")
    for job in java_jobs:
        print(f" - Title: {job['title']} | Company: {job['company']}")
        # Assert that 'java' is in title or company, and not just in description
        title_lower = (job['title'] or "").lower()
        company_lower = (job['company'] or "").lower()
        desc_lower = (job['description'] or "").lower()
        has_in_title_or_company = "java" in title_lower or "java" in company_lower
        has_only_in_desc = "java" in desc_lower and not has_in_title_or_company
        print(f"   In title/company? {has_in_title_or_company} | Only in desc? {has_only_in_desc}")
        assert has_in_title_or_company, "Error: Job matched java but 'java' is not in title or company!"

    print("\n--- Testing settings-based filtering in main.py logic simulation ---")
    # Simulate api_get_jobs settings filtering
    settings = get_all_settings()
    settings_terms_str = settings.get("search_terms", "")
    print(f"Settings search terms: '{settings_terms_str}'")
    settings_words = [w.lower().strip() for w in settings_terms_str.split(",") if w.strip()]
    print(f"Parsed terms: {settings_words}")
    
    all_jobs = get_jobs()
    print(f"Total jobs in DB: {len(all_jobs)}")
    
    filtered_count = 0
    for job in all_jobs:
        title_lower = (job.get("title") or "").lower()
        company_lower = (job.get("company") or "").lower()
        desc_lower = (job.get("description") or "").lower()
        
        matches_description_only = False
        matches_title_company = False
        
        if settings_words:
            matches_title_company = any(term in title_lower or term in company_lower for term in settings_words)
            matches_description_only = any(term in desc_lower for term in settings_words) and not matches_title_company
            
            if matches_title_company:
                filtered_count += 1
                
        if matches_description_only:
            print(f"Exclude pollution match: {job.get('title')} @ {job.get('company')} (matches terms in description only)")
            
    print(f"Filtered jobs matching settings (title/company only): {filtered_count} out of {len(all_jobs)}")
    
    print("\nSUCCESS: Search filtering verification tests passed!")

if __name__ == "__main__":
    run_tests()
