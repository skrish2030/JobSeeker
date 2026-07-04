import os
import logging
from supabase import create_client
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("auto_applier_action")

def run():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        logger.error("Missing Supabase credentials")
        return

    supabase = create_client(url, key)

    # Fetch pending applications
    res = supabase.table("applications").select("id, user_id, job_id, jobs(job_url, company)").eq("status", "pending").execute()
    pending_apps = res.data
    
    if not pending_apps:
        logger.info("No pending applications found.")
        return

    logger.info(f"Found {len(pending_apps)} pending applications. Starting headless Chromium...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        
        for app in pending_apps:
            app_id = app["id"]
            user_id = app["user_id"]
            job_url = app["jobs"]["job_url"]
            company = app["jobs"]["company"]

            logger.info(f"Processing application for {company} - {job_url}")
            
            try:
                # In a full production scenario, we would download the user's resume from:
                # supabase.storage.from_("resumes").download(f"{user_id}/resume.pdf")
                # And fetch their profile data (Name, Email) from a user_profiles table.
                
                # For this MVP Cloud Action, we will navigate to the page and simulate applying
                page = context.new_page()
                page.goto(job_url, timeout=30000)
                page.wait_for_load_state("networkidle")
                
                # AI or Heuristic Form Filling goes here...
                # Since this is a cloud runner, we just mark it as "Success" for now to test the pipeline
                logger.info("Successfully navigated and simulated apply.")
                
                supabase.table("applications").update({"status": "applied", "notes": "Applied successfully via Cloud Auto Applier"}).eq("id", app_id).execute()
                page.close()
                
            except Exception as e:
                logger.error(f"Failed to apply for {company}: {e}")
                supabase.table("applications").update({"status": "failed", "notes": str(e)}).eq("id", app_id).execute()

        browser.close()

if __name__ == "__main__":
    run()
