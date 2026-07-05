import os
import logging
import json
from datetime import datetime, timedelta
from supabase import create_client, Client
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("daily_ai_analysis")

def get_supabase() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
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
    analytics_res = supabase.table("analytics_insights").select("id, trending_skills, trending_titles").eq("is_latest", True).limit(1).execute()
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
        "interview process": 0,
        "udemy mentions": 0,
        "coursera mentions": 0,
        "github / open source": 0,
        "stackoverflow": 0
    }
    
    skill_counts = {}
    broad_skills = ["python", "react", "javascript", "java", "c++", "aws", "docker", "sql", "sas", "node", "typescript"]
    
    for item in feed_data:
        source = item.get("source_type", "unknown")
        if source == "reddit": reddit_count += 1
        elif source == "youtube": youtube_count += 1
        
        text = str(item.get("content_summary", "")).lower()
        
        # Categorize topics and platforms
        if "layoff" in text or "freeze" in text or "fired" in text: topic_counts["layoffs / hiring freezes"] += 1
        if "offer" in text or "hired" in text or "passed" in text: topic_counts["getting hired / offers"] += 1
        if "ai" in text or "chatgpt" in text or "replace" in text: topic_counts["AI taking jobs"] += 1
        if "remote" in text or "wfh" in text or "return to office" in text: topic_counts["remote work"] += 1
        if "interview" in text or "leetcode" in text: topic_counts["interview process"] += 1
        if "udemy" in text: topic_counts["udemy mentions"] += 1
        if "coursera" in text or "edx" in text: topic_counts["coursera mentions"] += 1
        if "github" in text: topic_counts["github / open source"] += 1
        if "stackoverflow" in text or "stack overflow" in text: topic_counts["stackoverflow"] += 1
            
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
    
    Based on this combined dataset, you MUST output a raw JSON object containing exactly two keys:
    1. "market_mood": A single, high-impact sentence summarizing the overall mood right now (e.g. "The market is heavily focused on AI anxieties but hiring remains strong for robust engineering fundamentals.").
    2. "trending_topics": An array of up to 5 objects showing the hottest topics being discussed in the community. Format: [{{"topic": "AI taking jobs", "heat_score": 85}}, {{"topic": "Remote work", "heat_score": 40}}].
    
    Output ONLY the raw JSON object. Do not include markdown formatting blocks like ```json.
    """
    
    try:
        logger.info("Calling Gemini API...")
        resp = model.generate_content(prompt)
        ai_summary = resp.text.strip()
        if ai_summary.startswith("```json"):
            ai_summary = ai_summary.replace("```json", "").replace("```", "").strip()
            
        # 4. Save to Database
        if analytics_res.data:
            latest_id = analytics_res.data[0].get("id")
            if latest_id:
                supabase.table("analytics_insights").update({
                    "ai_market_summary": ai_summary
                }).eq("id", latest_id).execute()
                logger.info("Successfully updated the frontend with the new Daily AI JSON Summary!")
        else:
            supabase.table("analytics_insights").insert({
                "ai_market_summary": ai_summary,
                "is_latest": True,
                "trending_skills": [],
                "trending_titles": [],
                "total_jobs_analyzed": 0
            }).execute()
            logger.info("Successfully created a NEW Daily AI JSON Summary because no job data existed!")
    except Exception as e:
        logger.error(f"Failed to generate or save AI analysis: {e}")

if __name__ == "__main__":
    run_daily_ai_analysis()
