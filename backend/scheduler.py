import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from backend.database import get_all_settings
from backend.scraper import run_scraper_cycle
from backend.email_service import send_jobs_digest_email

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scheduler")

# Global scheduler reference
_scheduler = None

def get_scheduler_status():
    """Returns status metrics of the background scheduler and scheduled jobs."""
    global _scheduler
    if not _scheduler or not _scheduler.running:
        return {"running": False, "jobs": []}
        
    jobs_info = []
    for job in _scheduler.get_jobs():
        jobs_info.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": str(job.next_run_time) if job.next_run_time else "None",
            "trigger": str(job.trigger)
        })
        
    return {
        "running": True,
        "jobs": jobs_info
    }

def check_and_run_notifications():
    """Checks all active profiles and dispatches notifications if they are due based on settings."""
    from backend.database import get_all_users_profiles, get_all_settings, active_user_id_var, active_profile_id_var
    from backend.email_service import send_jobs_digest_email
    from datetime import datetime, timedelta
    
    try:
        profiles = get_all_users_profiles()
    except Exception as e:
        logger.error(f"Failed to fetch profiles for scheduler run: {e}")
        return
        
    logger.info(f"[SCHEDULER] Checking notification triggers for {len(profiles)} profiles...")
    
    for p in profiles:
        user_id = p['user_id']
        profile_id = p['id']
        
        user_token = active_user_id_var.set(user_id)
        profile_token = active_profile_id_var.set(profile_id)
        try:
            settings = get_all_settings()
            opted_in = settings.get("email_notifications_enabled", "false") == "true"
            if not opted_in:
                continue
                
            frequency = settings.get("email_frequency", "daily") # hourly, daily, weekly
            last_run_str = settings.get("last_emailed_time", "")
            
            is_due = False
            if not last_run_str:
                is_due = True
            else:
                try:
                    last_run = datetime.fromisoformat(last_run_str)
                    elapsed = datetime.now() - last_run
                    if frequency == "hourly" and elapsed >= timedelta(hours=1):
                        is_due = True
                    elif frequency == "daily" and elapsed >= timedelta(days=1):
                        is_due = True
                    elif frequency == "weekly" and elapsed >= timedelta(days=7):
                        is_due = True
                except Exception as ex:
                    logger.error(f"Error parsing last_emailed_time for profile {p['name']}: {ex}")
                    is_due = True
                    
            if is_due:
                logger.info(f"[SCHEDULER] Profile '{p['name']}' digest is due (freq: {frequency}). Dispatching...")
                try:
                    send_jobs_digest_email()
                except Exception as ex:
                    logger.error(f"Failed to send scheduled digest for profile {p['name']}: {ex}")
        except Exception as e:
            logger.error(f"Error checking notifications for profile {p['name']}: {e}")
        finally:
            active_user_id_var.reset(user_token)
            active_profile_id_var.reset(profile_token)

def run_scheduled_scrape():
    """Runs the background scraper cycle for all active profiles."""
    logger.info("[SCHEDULER] Starting background scraper 30-minute cycle...")
    try:
        total_found, total_new = run_scraper_cycle()
        logger.info(f"[SCHEDULER] Scraper 30-minute cycle complete. Found: {total_found}, Saved: {total_new} new jobs.")
    except Exception as e:
        logger.error(f"[SCHEDULER] Scraper 30-minute cycle failed: {e}")

def start_scheduler():
    """Starts the background scheduler check loop."""
    global _scheduler
    if _scheduler and _scheduler.running:
        logger.info("Scheduler already running.")
        return
        
    _scheduler = BackgroundScheduler()
    
    logger.info("Initializing scheduler check loop running every 5 minutes and scraper every 30 minutes.")
    
    _scheduler.add_job(
        check_and_run_notifications,
        trigger=IntervalTrigger(minutes=5),
        id="notifications_job",
        name="Email Notifications Checker",
        replace_existing=True
    )
    
    _scheduler.add_job(
        run_scheduled_scrape,
        trigger=IntervalTrigger(minutes=30),
        id="scraper_job",
        name="Background Scraper Job",
        replace_existing=True,
        next_run_time=datetime.now() + timedelta(seconds=5)
    )
    
    _scheduler.start()
    logger.info("Scheduler started successfully in the background.")

def shutdown_scheduler():
    """Safely shuts down the scheduler if running."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown()
        logger.info("Scheduler stopped.")

def restart_scheduler():
    """Reloads scheduler checks by restarting the job."""
    global _scheduler
    logger.info("Reloading scheduler...")
    
    from backend.database import IS_LAMBDA
    if IS_LAMBDA:
        logger.info("Running in Lambda context. Skipping scheduler restart.")
        return
        
    if not _scheduler or not _scheduler.running:
        start_scheduler()
        return
        
    try:
        _scheduler.reschedule_job(
            "notifications_job",
            trigger=IntervalTrigger(minutes=5)
        )
        logger.info("Scheduler re-registered notifications trigger.")
    except Exception as e:
        logger.error(f"Failed to reschedule notifications job: {e}")
        try:
            _scheduler.shutdown(wait=False)
        except Exception:
            pass
        _scheduler = None
        start_scheduler()
