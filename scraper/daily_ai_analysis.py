import os
import logging
import json
from datetime import datetime, timedelta
from supabase import create_client, Client
import google.generativeai as genai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("daily_ai_analysis")

def get_supabase() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") # Use role key for full access
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
    return create_client(url, key)

def run_daily_ai_analysis():
    logger.info("Starting Daily Gemini AI Analysis...")
    supabase = get_supabase()
    
    ai_api_key = os.environ.get("GOOGLE_API_KEY")
    if not ai_api_key:
        logger.error("GOOGLE_API_KEY is missing. Cannot run Daily AI.")
        return
        
    genai.configure(api_key=ai_api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    # 1. Fetch yesterday's data from Intelligence Feed (Reddit + YouTube)
    yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat()
    logger.info(f"Fetching intelligence data created after {yesterday}...")
    
    feed_res = supabase.table("intelligence_feed").select("source_type, content_summary").gte("created_at", yesterday).execute()
    feed_data = feed_res.data
    
    if not feed_data:
        logger.warning("No new intelligence data (Reddit/YouTube) found from yesterday.")
        feed_data = [{"source_type": "none", "content_summary": "No community discussions found today."}]
        
    # 2. Fetch yesterday's Job Trends (just the top roles/skills)
    # We will grab the latest analytics_insights local generation as our baseline
    analytics_res = supabase.table("analytics_insights").select("id, trending_skills, trending_titles").order("created_at", desc=True).limit(1).execute()
    jobs_data = analytics_res.data[0] if analytics_res.data else {"trending_skills": [], "trending_titles": []}
    
    # 3. Construct massive context for Gemini
    prompt = f"""
    You are an elite Silicon Valley Tech Recruiter and Job Market Analyst.
    Your task is to provide the ultimate DAILY MARKET REPORT.
    
    Below is the raw data collected from scraping the web over the last 24 hours.
    
    --- 1. JOB BOARD TRENDS (from Indeed, LinkedIn, etc.) ---
    Top Titles Hiring Now: {json.dumps(jobs_data.get("trending_titles", []))}
    Most Requested Skills: {json.dumps(jobs_data.get("trending_skills", []))}
    
    --- 2. COMMUNITY PULSE (from Reddit & YouTube transcripts) ---
    {json.dumps(feed_data, indent=2)}
    
    Based on this combined dataset, write a highly engaging, professional 3-paragraph "Daily AI Market Analysis".
    - Paragraph 1: What is the overall mood right now (layoffs, hiring boom, AI anxiety)?
    - Paragraph 2: What are the hottest jobs and specific skills that employers are actively paying for today?
    - Paragraph 3: What is your strategic advice to job seekers based on what people on YouTube/Reddit are saying vs what employers actually want?
    
    Do not use markdown blocks, just return the text.
    """
    
    try:
        logger.info("Calling Gemini API...")
        resp = model.generate_content(prompt)
        ai_summary = resp.text.strip()
        
        # 4. Save to Database
        # We will update the latest analytics_insights row to include this AI summary
        if analytics_res.data:
            latest_id = analytics_res.data[0].get("id")
            if latest_id:
                supabase.table("analytics_insights").update({
                    "ai_market_summary": f"🤖 AI Daily Report: {ai_summary}"
                }).eq("id", latest_id).execute()
                logger.info("Successfully updated the frontend with the new Daily AI Summary!")
            else:
                logger.warning("Could not find ID to update analytics_insights.")
    except Exception as e:
        logger.error(f"Failed to generate or save AI analysis: {e}")

if __name__ == "__main__":
    run_daily_ai_analysis()
