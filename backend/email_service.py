import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

from backend.database import (
    get_all_settings,
    get_jobs_to_email,
    mark_jobs_as_emailed
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("email_service")

def get_email_location(job):
    """Parses location to output either 'Remote', 'Hybrid', the US State code, or 'Other'."""
    rt = (job.get("remote_type") or "").lower()
    if rt == "remote":
        return "Remote"
    if rt == "hybrid":
        return "Hybrid"
    
    # Extract state abbreviation (e.g. CA, NY, DE)
    loc = job.get("location") or ""
    parts = [p.strip() for p in loc.split(",") if p.strip()]
    for p in parts:
        if len(p) == 2 and p.isupper() and p.isalpha():
            return p
    if len(parts) > 1:
        if len(parts[-2]) == 2 and parts[-2].isupper():
            return parts[-2]
        return parts[-1]
    return loc or "Other"

def build_job_table_row(job, idx):
    """Generates a table row for a single job match."""
    bg_color = "#f9fafb" if idx % 2 == 0 else "#ffffff"
    location = get_email_location(job)
    
    # Direct portal URL takes priority, fall back to scraped job URL
    website_url = job.get("company_portal_url") or job.get("job_url") or "#"
    website_label = "Career Portal" if job.get("company_portal_url") else "Job Source"
    
    return f"""
    <tr style="background-color: {bg_color}; border-bottom: 1px solid #e5e7eb; font-size: 13px; color: #374151;">
        <td style="padding: 12px 16px; font-weight: 600; color: #1f2937;">{job['company']}</td>
        <td style="padding: 12px 16px;">
            <a href="{job['job_url']}" style="color: #4f46e5; text-decoration: none; font-weight: 500;" target="_blank">
                {job['title']}
            </a>
        </td>
        <td style="padding: 12px 16px; font-weight: 500;">{location}</td>
        <td style="padding: 12px 16px;">
            <a href="{website_url}" style="color: #4f46e5; text-decoration: none; font-weight: 600;" target="_blank">
                {website_label} <span style="font-size: 10px;">&#8599;</span>
            </a>
        </td>
    </tr>
    """

def send_jobs_digest_email(force_db_only=False):
    """Unified scrape-and-email run:
    1. Scrapes new jobs matching profile settings (unless force_db_only).
    2. Classifies/scores them using AI.
    3. Filter out previously emailed ones using emailed_job_hashes.
    4. Sends HTML email.
    5. Saves updated emailed_job_hashes to settings.
    """
    import hashlib
    import os
    settings = get_all_settings()
    sender = os.environ.get("SMTP_SENDER") or settings.get("email_sender", "")
    password = os.environ.get("SMTP_PASSWORD") or settings.get("email_sender_password", "")
    recipient = settings.get("email_recipient", "")
    smtp_server = os.environ.get("SMTP_SERVER") or settings.get("email_smtp_server", "")
    smtp_port_str = os.environ.get("SMTP_PORT") or settings.get("email_smtp_port", "587")
    
    if not sender or not password or not recipient or not smtp_server:
        logger.warning("Email settings are incomplete. Skipping email dispatch.")
        return 0
        
    if force_db_only:
        logger.info("Forcing DB-only email digest. Skipping scraper cycle.")
        from backend.database import db
        classified_jobs = list(db.jobs.find().sort("posted_date", -1).limit(200))
    else:
        from backend.scraper import _execute_scraper_cycle
        logger.info("Running scraper to fetch new jobs for email digest...")
        try:
            found_count, classified_jobs = _execute_scraper_cycle()
        except Exception as e:
            logger.error(f"Failed to execute scraper cycle for email digest: {e}")
            return 0
            
    if not isinstance(classified_jobs, list):
        logger.warning(f"Scraper returned invalid result: {type(classified_jobs)}")
        return 0
        
    min_score = int(settings.get("min_relevance_score", "50"))
    
    # Load emailed job hashes to avoid duplicate email notifications
    emailed_hashes_str = settings.get("emailed_job_hashes", "")
    emailed_hashes = set() if force_db_only else set(h.strip() for h in emailed_hashes_str.split(",") if h.strip())
    
    alert_titles_str = settings.get("email_alert_job_title", "")
    alert_locations_str = settings.get("email_alert_location", "")
    alert_titles = [t.strip().lower() for t in alert_titles_str.split(",") if t.strip()]
    alert_locations = [l.strip().lower() for l in alert_locations_str.split(",") if l.strip()]
    
    eligible_jobs = []
    
    for job in classified_jobs:
        score = int(job.get("score", 0))
        job_url = job.get("job_url", "")
        job_hash = hashlib.md5(job_url.encode('utf-8')).hexdigest() if job_url else None
        
        title_lower = (job.get("title") or "").lower()
        company_lower = (job.get("company") or "").lower()
        loc_lower = (job.get("location") or "").lower()
        
        matches_alert_title = True
        if alert_titles:
            matches_alert_title = any(t in title_lower or t in company_lower for t in alert_titles)
            
        matches_alert_location = True
        if alert_locations:
            matches_alert_location = any(l in loc_lower for l in alert_locations)
            
        if score >= min_score and job_hash and job_hash not in emailed_hashes and matches_alert_title and matches_alert_location:
            eligible_jobs.append((job, job_hash))
            
    from backend.database import get_safe_score
    eligible_jobs.sort(key=lambda x: (x[0].get("posted_date") or "", get_safe_score(x[0])), reverse=True)
    
    if alert_titles:
        eligible_jobs = eligible_jobs[:30]
    else:
        eligible_jobs = eligible_jobs[:20]
        
    jobs_to_email = [item[0] for item in eligible_jobs]
    new_emailed_hashes = [item[1] for item in eligible_jobs]
            
    if not jobs_to_email:
        logger.info("No new matching jobs to email. Skipping email send.")
        return 0
        
    logger.info(f"Sending email digest with {len(jobs_to_email)} new jobs to {recipient}...")
    
    # Create email envelope
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"[JobSeeker] {len(jobs_to_email)} New Match Roles (Scored >= {min_score})"
    msg['From'] = f"JobSeeker Command Center <{sender}>"
    msg['To'] = recipient
    
    # Generate table rows HTML
    rows_html = "\n".join(build_job_table_row(j, idx) for idx, j in enumerate(jobs_to_email))
    
    # Full template
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f3f4f6; margin: 0; padding: 0; }}
            .container {{ max-width: 650px; margin: 20px auto; padding: 20px; }}
            .header {{ text-align: center; padding: 20px 0; border-bottom: 2px solid #e5e7eb; background-color: #1e1b4b; border-radius: 8px 8px 0 0; color: #ffffff; }}
            .footer {{ text-align: center; padding: 20px 0; color: #6b7280; font-size: 12px; border-top: 1px solid #e5e7eb; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 style="margin: 0; font-size: 24px; font-weight: 800; letter-spacing: 0.5px;">JobSeeker Command Center</h1>
                <p style="margin: 5px 0 0 0; font-size: 14px; opacity: 0.9;">Personalized Match Digest</p>
            </div>
            
            <div style="padding: 20px 0;">
                <p style="font-size: 15px; color: #374151; margin-bottom: 20px;">
                    Hi! Based on your target profiles and resume settings, we have identified <strong>{len(jobs_to_email)} new match opportunities</strong>:
                </p>
                
                <table style="width: 100%; border-collapse: collapse; margin-top: 15px; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                    <thead>
                        <tr style="background-color: #312e81; color: #ffffff; text-align: left; font-size: 13px;">
                            <th style="padding: 12px 16px; font-weight: 600; width: 25%;">Company</th>
                            <th style="padding: 12px 16px; font-weight: 600; width: 40%;">Role</th>
                            <th style="padding: 12px 16px; font-weight: 600; width: 15%;">Location</th>
                            <th style="padding: 12px 16px; font-weight: 600; width: 20%;">Website</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>
            </div>
            
            <div class="footer">
                This is an automated notification from your local JobSeeker application running on your laptop.<br>
                To adjust search terms or email frequency, update settings in the JobSeeker web application.
            </div>
        </div>
    </body>
    </html>
    """
    
    msg.attach(MIMEText(html_content, 'html'))
    
    smtp_port = int(smtp_port_str)
    
    try:
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            
        server.login(sender, password)
        server.sendmail(sender, recipient, msg.as_string())
        server.quit()
        
        # Update emailed hashes list to prevent resending (cap at 400 hashes)
        updated_hashes = list(emailed_hashes) + new_emailed_hashes
        if len(updated_hashes) > 400:
            updated_hashes = updated_hashes[-400:]
            
        from backend.database import update_settings
        update_settings({
            "emailed_job_hashes": ",".join(updated_hashes),
            "last_emailed_time": datetime.now().isoformat()
        })
        
        logger.info(f"Email sent successfully. {len(jobs_to_email)} new jobs emailed.")
        return len(jobs_to_email)
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        raise e

def send_test_email(test_recipient):
    """Sends a simple test email to confirm SMTP configurations work correctly."""
    import os
    settings = get_all_settings()
    sender = os.environ.get("SMTP_SENDER") or settings.get("email_sender", "")
    password = os.environ.get("SMTP_PASSWORD") or settings.get("email_sender_password", "")
    smtp_server = os.environ.get("SMTP_SERVER") or settings.get("email_smtp_server", "")
    smtp_port_str = os.environ.get("SMTP_PORT") or settings.get("email_smtp_port", "587")
    
    if not sender or not password or not smtp_server:
        raise ValueError("SMTP configuration settings are missing.")
        
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "[JobSeeker] SMTP Configuration Test"
    msg['From'] = f"JobSeeker Test <{sender}>"
    msg['To'] = test_recipient
    
    html_content = f"""
    <html>
    <body>
        <h2>SMTP Setup Verified!</h2>
        <p>This is a test email from your JobSeeker desktop application.</p>
        <p>If you received this message, your SMTP credentials and connection are properly configured.</p>
        <p>Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </body>
    </html>
    """
    msg.attach(MIMEText(html_content, 'html'))
    
    smtp_port = int(smtp_port_str)
    if smtp_port == 465:
        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
    else:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        
    server.login(sender, password)
    server.sendmail(sender, test_recipient, msg.as_string())
    server.quit()
    logger.info(f"Test email successfully dispatched to {test_recipient}.")

from backend.database import get_master_settings

def send_mfa_code_email(recipient_email, username, mfa_code):
    """Sends a 6-digit MFA OTP validation code to the user's email."""
    import os
    print(f"[MFA EMAIL] Starting send_mfa_code_email to {recipient_email} for user {username}")
    settings = get_master_settings()
    sender = os.environ.get("SMTP_SENDER") or settings.get("email_sender", "")
    password = os.environ.get("SMTP_PASSWORD") or settings.get("email_sender_password", "")
    smtp_server = os.environ.get("SMTP_SERVER") or settings.get("email_smtp_server", "")
    smtp_port_str = os.environ.get("SMTP_PORT") or settings.get("email_smtp_port", "587")
    
    print(f"[MFA EMAIL CONFIG] sender={sender}, smtp_server={smtp_server}, smtp_port={smtp_port_str}")
    
    if not sender or not password or not smtp_server:
        print(f"[MFA EMAIL WARNING] Master SMTP not configured. MFA code [{mfa_code}] printed to console instead.")
        logger.warning(f"Master SMTP not configured. MFA code [{mfa_code}] printed to console instead.")
        return False
        
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"[JobSeeker] Your 6-Digit Verification Code: {mfa_code}"
    msg['From'] = f"JobSeeker Auth <{sender}>"
    msg['To'] = recipient_email
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f3f4f6; margin: 0; padding: 0; }}
            .container {{ max-width: 500px; margin: 30px auto; padding: 25px; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }}
            .header {{ text-align: center; border-bottom: 2px solid #e5e7eb; padding-bottom: 15px; margin-bottom: 20px; }}
            .code-box {{ text-align: center; background-color: #f3f0ff; border: 1px solid #dcd3ff; padding: 15px; border-radius: 8px; font-size: 32px; font-weight: 800; letter-spacing: 4px; color: #7c4dff; margin: 25px 0; }}
            .footer {{ text-align: center; font-size: 11px; color: #9ca3af; margin-top: 25px; border-top: 1px solid #e5e7eb; padding-top: 15px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2 style="color: #1f2937; margin: 0;">JobSeeker Authentication</h2>
            </div>
            <p style="color: #4b5563; font-size: 14px; line-height: 20px;">
                Hello <strong>{username}</strong>,<br><br>
                A request has been made to log in to your JobSeeker account. Use the verification code below to authorize your session:
            </p>
            
            <div class="code-box">{mfa_code}</div>
            
            <p style="color: #6b7280; font-size: 12px; line-height: 18px;">
                This code is temporary and will expire in 10 minutes. If you did not initiate this request, you can safely ignore this email.
            </p>
            
            <div class="footer">
                JobSeeker Security Service
            </div>
        </div>
    </body>
    </html>
    """
    msg.attach(MIMEText(html_content, 'html'))
    
    try:
        smtp_port = int(smtp_port_str)
        print(f"[MFA EMAIL CONNECT] Connecting to {smtp_server}:{smtp_port}...")
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            
        print("[MFA EMAIL LOGIN] Logging in...")
        server.login(sender, password)
        print("[MFA EMAIL SEND] Sending mail...")
        server.sendmail(sender, recipient_email, msg.as_string())
        server.quit()
        print(f"[MFA EMAIL SUCCESS] MFA verification email successfully sent to {recipient_email}.")
        logger.info(f"MFA verification email successfully sent to {recipient_email}.")
        return True
    except Exception as e:
        print(f"[MFA EMAIL ERROR] Failed to send MFA email to {recipient_email}: {str(e)}")
        logger.error(f"Failed to send MFA email to {recipient_email}: {str(e)}")
        return False
