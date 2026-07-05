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
    
    # 2b. Aggregate and categorize community pulse to save AI tokens
    reddit_count = 0
    youtube_count = 0
    
    # Categorization buckets
    topic_counts = {
        "layoffs / hiring freezes": 0,
        "getting hired / offers": 0,
        "AI taking jobs": 0,
        "remote work": 0,
        "interview process": 0
    }
    
    skill_counts = {}
    broad_skills = ["python", "react", "javascript", "java", "c++", "aws", "docker", "sql", "sas", "node", "typescript"]
    
    for item in feed_data:
        source = item.get("source_type", "unknown")
        if source == "reddit": reddit_count += 1
        elif source == "youtube": youtube_count += 1
        
        text = str(item.get("content_summary", "")).lower()
        
        # Categorize topics
        if "layoff" in text or "freeze" in text or "fired" in text: topic_counts["layoffs / hiring freezes"] += 1
        if "offer" in text or "hired" in text or "passed" in text: topic_counts["getting hired / offers"] += 1
        if "ai" in text or "chatgpt" in text or "replace" in text: topic_counts["AI taking jobs"] += 1
        if "remote" in text or "wfh" in text or "return to office" in text: topic_counts["remote work"] += 1
        if "interview" in text or "leetcode" in text: topic_counts["interview process"] += 1
            
        # Count skills
        for skill in broad_skills:
            if skill in text:
                skill_counts[skill] = skill_counts.get(skill, 0) + 1
                
    community_summary = {
        "total_discussions_analyzed": reddit_count + youtube_count,
        "reddit_posts": reddit_count,
        "youtube_videos": youtube_count,
        "trending_discussion_topics": topic_counts,
        "most_discussed_skills": skill_counts
    }
    
    # 3. Construct context for Gemini
    prompt = f"""
    You are an elite Silicon Valley Tech Recruiter and Job Market Analyst.
    Your task is to provide the ultimate DAILY MARKET REPORT.
    
    Below is the categorized, statistical data collected from scraping the web over the last 24 hours.
    
    --- 1. JOB BOARD TRENDS (from Indeed, LinkedIn, etc.) ---
    Top Titles Hiring Now: {json.dumps(jobs_data.get("trending_titles", []))}
    Most Requested Skills: {json.dumps(jobs_data.get("trending_skills", []))}
    
    --- 2. COMMUNITY PULSE (Aggregated from Reddit & YouTube) ---
    {json.dumps(community_summary, indent=2)}
    
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
