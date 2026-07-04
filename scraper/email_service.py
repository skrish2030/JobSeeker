import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from supabase import create_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("email_service")

def send_jobs_digest_email():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        logger.error("Missing Supabase credentials")
        return

    supabase = create_client(url, key)

    # Email Settings
    sender = os.environ.get("SMTP_SENDER")
    password = os.environ.get("SMTP_PASSWORD")
    # For a personal project, send to the same email
    recipient = os.environ.get("SMTP_RECIPIENT", sender) 
    
    if not sender or not password:
        logger.warning("SMTP_SENDER or SMTP_PASSWORD not set. Skipping email dispatch.")
        return

    # Check which users have email notifications enabled
    users_res = supabase.table("user_settings").select("user_id, target_job_title, target_location").eq("email_notifications", True).execute()
    
    if not users_res.data:
        logger.info("No users have email notifications enabled.")
        return

    # Get jobs scraped in the last 24 hours with high scores
    yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat()
    jobs_res = supabase.table("jobs").select("*").gte("created_at", yesterday).order("score", desc=True).limit(20).execute()
    jobs = jobs_res.data

    if not jobs:
        logger.info("No new jobs found in the last 24 hours to email.")
        return

    logger.info(f"Found {len(jobs)} recent high-scoring jobs. Preparing email digest...")

    # Build HTML Rows
    rows = ""
    for idx, job in enumerate(jobs):
        bg_color = "#f9fafb" if idx % 2 == 0 else "#ffffff"
        website_url = job.get("job_url") or "#"
        score = job.get("score", 0)
        
        rows += f"""
        <tr style="background-color: {bg_color}; border-bottom: 1px solid #e5e7eb; font-size: 13px; color: #374151;">
            <td style="padding: 12px 16px; font-weight: 600; color: #1f2937;">{job.get('company')}</td>
            <td style="padding: 12px 16px;">
                <a href="{website_url}" style="color: #4f46e5; text-decoration: none; font-weight: 500;" target="_blank">
                    {job.get('title')}
                </a>
            </td>
            <td style="padding: 12px 16px; font-weight: 500;">{job.get('location')}</td>
            <td style="padding: 12px 16px; font-weight: bold; color: {'#10b981' if score >= 80 else '#f59e0b'};">{score}%</td>
            <td style="padding: 12px 16px;">
                <a href="{website_url}" style="display: inline-block; padding: 6px 12px; background-color: #4f46e5; color: white; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 11px;" target="_blank">
                    Apply Now ↗
                </a>
            </td>
        </tr>
        """

    html_content = f"""
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f3f4f6; margin: 0; padding: 20px;">
        <div style="max-w: 800px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
            <div style="background-color: #4f46e5; padding: 24px; text-align: center;">
                <h1 style="color: #ffffff; margin: 0; font-size: 24px;">JobSeeker Daily Digest 🚀</h1>
                <p style="color: #e0e7ff; margin: 8px 0 0 0; font-size: 14px;">Here are your top matching jobs for today.</p>
            </div>
            
            <div style="padding: 24px;">
                <table style="width: 100%; border-collapse: collapse; text-align: left;">
                    <thead>
                        <tr style="background-color: #f8fafc; border-bottom: 2px solid #e2e8f0; color: #64748b; font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em;">
                            <th style="padding: 12px 16px;">Company</th>
                            <th style="padding: 12px 16px;">Job Title</th>
                            <th style="padding: 12px 16px;">Location</th>
                            <th style="padding: 12px 16px;">Match</th>
                            <th style="padding: 12px 16px;">Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows}
                    </tbody>
                </table>
            </div>
            
            <div style="background-color: #f8fafc; padding: 16px; text-align: center; border-top: 1px solid #e2e8f0;">
                <p style="color: #64748b; font-size: 12px; margin: 0;">You received this email because you have Email Notifications enabled in JobSeeker Settings.</p>
            </div>
        </div>
    </body>
    </html>
    """

    # Send the email
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"JobSeeker Daily Digest: {len(jobs)} New Matches"
    msg["From"] = f"JobSeeker <{sender}>"
    msg["To"] = recipient

    msg.attach(MIMEText(html_content, "html"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, recipient, msg.as_string())
        server.quit()
        logger.info(f"Successfully sent daily digest email to {recipient}")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")

if __name__ == "__main__":
    send_jobs_digest_email()
