import os
import time
import logging
from playwright.sync_api import sync_playwright
from backend.ats_scraper import extract_slug_from_url

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("auto_applier")

def fill_form_field(page, label_text, value):
    """
    Heuristically attempts to fill a form field based on its label text.
    Tolerant to minor selector misses.
    """
    if not value:
        return False
    try:
        # Try finding by label text in Playwright
        loc = page.get_by_label(label_text, exact=False)
        if loc.count() > 0:
            loc.first.fill(value)
            logger.info(f"Filled field by label '{label_text}'")
            return True
            
        # Try finding by placeholder
        loc = page.get_by_placeholder(label_text, exact=False)
        if loc.count() > 0:
            loc.first.fill(value)
            logger.info(f"Filled field by placeholder '{label_text}'")
            return True
            
        # Try selector heuristics using XPath or text contains
        selectors = [
            f"input[name*='{label_text.lower()}']",
            f"input[id*='{label_text.lower()}']",
            f"//label[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{label_text.lower()}')]/following-sibling::input",
            f"//label[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{label_text.lower()}')]/ancestor::div[1]//input"
        ]
        for sel in selectors:
            loc = page.locator(sel)
            if loc.count() > 0:
                loc.first.fill(value)
                logger.info(f"Filled field by selector heuristic '{sel}' for label '{label_text}'")
                return True
    except Exception as e:
        logger.warning(f"Failed to fill field '{label_text}': {e}")
    return False

def run_auto_apply(job_url, company_name, profile, mode="preview"):
    """
    Launches Playwright to fill out and submit the application for a job.
    
    profile keys:
      - candidate_first_name
      - candidate_last_name
      - candidate_email
      - candidate_phone
      - candidate_linkedin
      - candidate_github
      - candidate_portfolio
      - resume_file_path
    """
    slug, platform = extract_slug_from_url(job_url, company_name)
    logger.info(f"Initiating auto-apply to {company_name} ({job_url}) on platform '{platform}' (mode: {mode})")
    
    resume_path = profile.get("resume_file_path") or ""
    if not resume_path or not os.path.exists(resume_path):
        return {"status": "error", "message": f"Resume file path '{resume_path}' does not exist on your local disk. Please check your settings."}
        
    headless = True if mode == "auto" else False
    
    with sync_playwright() as p:

        last_error = None
        for browser_engine in [p.chromium, p.firefox, p.webkit]:
            try:
                logger.info(f"Attempting automation with {browser_engine.name}...")
                browser = browser_engine.launch(headless=headless)
                context = browser.new_context(
                    viewport={"width": 1280, "height": 800},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = context.new_page()
                
                page.goto(job_url, timeout=30000)
                page.wait_for_load_state("networkidle")
                
                if platform == "greenhouse":
                    # Fill basic details
                    fill_form_field(page, "First Name", profile.get("candidate_first_name"))
                    fill_form_field(page, "Last Name", profile.get("candidate_last_name"))
                    fill_form_field(page, "Email", profile.get("candidate_email"))
                    fill_form_field(page, "Phone", profile.get("candidate_phone"))
                    
                    # Fill social/profile urls
                    fill_form_field(page, "LinkedIn", profile.get("candidate_linkedin"))
                    fill_form_field(page, "GitHub", profile.get("candidate_github"))
                    fill_form_field(page, "Website", profile.get("candidate_portfolio"))
                    fill_form_field(page, "Portfolio", profile.get("candidate_portfolio"))
                    
                    # Upload resume
                    try:
                        # Find Greenhouse file input (often has id="resume_file" or type="file")
                        file_input = page.locator("input[type='file'][id*='resume']").first
                        if file_input.count() > 0:
                            file_input.set_input_files(resume_path)
                            logger.info("Successfully uploaded resume to Greenhouse form")
                except Exception as e:
                    logger.warning(f"Failed to upload resume to Greenhouse form: {e}")
                
                # Heuristically accept GDPR/Consent if present
                try:
                    gdpr_checkbox = page.locator("input[type='checkbox'][name*='gdpr']").first
                    if gdpr_checkbox.count() > 0 and not gdpr_checkbox.is_checked():
                        gdpr_checkbox.check()
                        logger.info("Checked GDPR consent checkbox")
                except Exception:
                    pass
                
                # Auto or Preview actions
                if mode == "auto":
                    submit_btn = page.locator("#submit_app").first
                    if submit_btn.count() > 0:
                        submit_btn.click()
                        page.wait_for_navigation(timeout=10000)
                        logger.info("Submitted Greenhouse application successfully")
                        return {"status": "success", "message": "Successfully submitted application to Greenhouse!"}
                    else:
                        return {"status": "error", "message": "Could not find submission button '#submit_app'"}
                else:
                    # Keep browser open for user review
                    logger.info("Form filled. Pausing browser in headed preview mode...")
                    time.sleep(300) # Give 5 minutes for review
                    return {"status": "preview", "message": "Form filled in headed preview. Review form in opened window."}
                    
            elif platform == "lever":
                # Check if we need to click the initial Apply button
                apply_button = page.locator("a.postings-btn[href*='/apply']").first
                if apply_button.count() > 0:
                    apply_button.click()
                    page.wait_for_load_state("networkidle")
                
                # Fill basic details
                fill_form_field(page, "Full Name", f"{profile.get('candidate_first_name', '')} {profile.get('candidate_last_name', '')}".strip())
                fill_form_field(page, "Email", profile.get("candidate_email"))
                fill_form_field(page, "Phone", profile.get("candidate_phone"))
                
                # Lever custom name selectors
                try: page.locator("input[name='name']").first.fill(f"{profile.get('candidate_first_name', '')} {profile.get('candidate_last_name', '')}".strip())
                except Exception: pass
                try: page.locator("input[name='email']").first.fill(profile.get("candidate_email", ""))
                except Exception: pass
                try: page.locator("input[name='phone']").first.fill(profile.get("candidate_phone", ""))
                except Exception: pass
                
                # Fill social/profile urls
                fill_form_field(page, "LinkedIn", profile.get("candidate_linkedin"))
                fill_form_field(page, "GitHub", profile.get("candidate_github"))
                fill_form_field(page, "Portfolio", profile.get("candidate_portfolio"))
                fill_form_field(page, "Other", profile.get("candidate_portfolio"))
                
                try: page.locator("input[name='urls[LinkedIn]']").first.fill(profile.get("candidate_linkedin", ""))
                except Exception: pass
                try: page.locator("input[name='urls[GitHub]']").first.fill(profile.get("candidate_github", ""))
                except Exception: pass
                try: page.locator("input[name='urls[Portfolio]']").first.fill(profile.get("candidate_portfolio", ""))
                except Exception: pass
                
                # Upload resume
                try:
                    file_input = page.locator("input[type='file'][id='resume-upload-input']").first
                    if file_input.count() > 0:
                        file_input.set_input_files(resume_path)
                        logger.info("Successfully uploaded resume to Lever form")
                except Exception as e:
                    logger.warning(f"Failed to upload resume to Lever form: {e}")
                    
                # Auto or Preview actions
                if mode == "auto":
                    submit_btn = page.locator("button[type='submit']").first
                    if submit_btn.count() > 0:
                        submit_btn.click()
                        page.wait_for_navigation(timeout=10000)
                        logger.info("Submitted Lever application successfully")
                        return {"status": "success", "message": "Successfully submitted application to Lever!"}
                    else:
                        return {"status": "error", "message": "Could not find submission button"}
                else:
                    # Keep browser open for user review
                    logger.info("Form filled. Pausing browser in headed preview mode...")
                    time.sleep(300)
                    return {"status": "preview", "message": "Form filled in headed preview. Review form in opened window."}
            
            else:
                # Fallback form filler for Ashby or general pages using label matching
                logger.info("Using fallback generic form filler...")
                
                # Fill common fields
                fill_form_field(page, "First Name", profile.get("candidate_first_name"))
                fill_form_field(page, "Last Name", profile.get("candidate_last_name"))
                fill_form_field(page, "Full Name", f"{profile.get('candidate_first_name', '')} {profile.get('candidate_last_name', '')}".strip())
                fill_form_field(page, "Email", profile.get("candidate_email"))
                fill_form_field(page, "Phone", profile.get("candidate_phone"))
                fill_form_field(page, "LinkedIn", profile.get("candidate_linkedin"))
                fill_form_field(page, "GitHub", profile.get("candidate_github"))
                fill_form_field(page, "Portfolio", profile.get("candidate_portfolio"))
                fill_form_field(page, "Website", profile.get("candidate_portfolio"))
                
                # Try locating file input
                try:
                    file_input = page.locator("input[type='file']").first
                    if file_input.count() > 0:
                        file_input.set_input_files(resume_path)
                        logger.info("Successfully uploaded resume to generic form")
                except Exception as e:
                    logger.warning(f"Failed to upload resume to generic form: {e}")
                    
                if mode == "auto":
                    # Try finding a submit button
                    submit_selectors = ["button[type='submit']", "input[type='submit']", "button:has-text('Submit')", "button:has-text('Apply')"]
                    submit_btn = None
                    for sel in submit_selectors:
                        loc = page.locator(sel).first
                        if loc.count() > 0:
                            submit_btn = loc
                            break
                    if submit_btn:
                        submit_btn.click()
                        page.wait_for_navigation(timeout=10000)
                        return {"status": "success", "message": "Generic auto-applier submitted form successfully."}
                    else:
                        return {"status": "error", "message": "Generic auto-applier filled the form but could not identify a submit button."}
                else:
                    logger.info("Generic form filled. Pausing browser in headed preview mode...")
                    time.sleep(300)
                    return {"status": "preview", "message": "Form filled in headed preview. Review form in opened window."}
                    
            except Exception as e:
                logger.warning(f"Playwright automation failed with {browser_engine.name}: {e}")
                last_error = e
                continue
            finally:
                try: browser.close()
                except Exception: pass
        
        logger.error(f"Playwright auto-apply failed on all browsers. Last error: {last_error}")
        return {"status": "error", "message": f"Playwright automation failed on all browsers: {str(last_error)}"}
