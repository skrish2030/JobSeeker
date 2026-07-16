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
    
    if not sender or not password:
        logger.warning("SMTP_SENDER or SMTP_PASSWORD not set. Skipping email dispatch.")
        return

    # Check which users have email notifications enabled
    users_res = supabase.table("user_settings").select("user_id, target_job_title, target_location").eq("email_notifications", True).execute()
    
    if not users_res.data:
        logger.info("No users have email notifications enabled.")
        return

    # Setup SMTP server once
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender, password)
    except Exception as e:
        logger.error(f"Failed to connect to SMTP server: {e}")
        return

    yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat()
    emails_sent = 0

    for user in users_res.data:
        user_id = user.get("user_id")
        recipient = None
        if user_id:
            try:
                auth_user_res = supabase.auth.admin.get_user_by_id(user_id)
                if auth_user_res and auth_user_res.user:
                    recipient = auth_user_res.user.email
            except Exception as e:
                logger.error(f"Failed to fetch email for user_id {user_id}: {e}")
                
        if not recipient:
            logger.warning(f"No valid email found for user ID: {user_id}")
            continue

        target_title = user.get("target_job_title", "")
        target_location = user.get("target_location", "")

        logger.info(f"Preparing digest for {recipient} ({target_title} in {target_location})...")

        # Get jobs scraped in the last 24 hours that match this user's location and keyword
        # Note: We use ilike to do case-insensitive substring matching
        query = supabase.table("jobs").select("*").gte("created_at", yesterday)
        if target_title:
            # We do a basic string match for the keyword in the job title or description
            # In Supabase REST API, ilike is supported.
            query = query.ilike("title", f"%{target_title}%")
        if target_location:
            query = query.ilike("location", f"%{target_location}%")
            
        jobs_res = query.order("score", desc=True).limit(20).execute()
        jobs = jobs_res.data

        if not jobs:
            logger.info(f"No new jobs found for {recipient}.")
            continue

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
                    <p style="color: #e0e7ff; margin: 8px 0 0 0; font-size: 14px;">Here are your top {len(jobs)} matches for {target_title}.</p>
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
                    <p style="color: #64748b; font-size: 12px; margin: 0;">You received this email because you enabled notifications in JobSeeker Settings.</p>
                </div>
            </div>
        </body>
        </html>
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"JobSeeker Daily Digest: {len(jobs)} New Matches"
        msg["From"] = f"JobSeeker <{sender}>"
        msg["To"] = recipient
        msg.attach(MIMEText(html_content, "html"))

        try:
            server.sendmail(sender, recipient, msg.as_string())
            emails_sent += 1
            logger.info(f"Successfully sent digest to {recipient}")
        except Exception as e:
            logger.error(f"Failed to send email to {recipient}: {e}")

    server.quit()
    logger.info(f"Completed! Sent {emails_sent} total emails.")

if __name__ == "__main__":
    send_jobs_digest_email()
