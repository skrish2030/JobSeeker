import os
import logging
from collections import Counter
import json
from datetime import datetime, timedelta
import pytz

# Fallback for Python versions before 3.11 that don't have datetime.UTC
UTC = getattr(datetime, "UTC", pytz.UTC)

from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("predictive_analytics")

def get_supabase() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
    return create_client(url, key)

def run_predictive_engine():
    supabase = get_supabase()
    yesterday = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    
    logger.info(f"Fetching community intelligence data created after {yesterday}...")
    intel_res = supabase.table("intelligence_feed").select("source_type, content_summary").gte("created_at", yesterday).execute()
    intel_data = intel_res.data
    
    analytics_res = supabase.table("analytics_insights").select("id, trending_skills, trending_titles").eq("is_latest", True).limit(1).execute()
    
    if not intel_data:
        logger.warning("No recent community intelligence found. Skipping prediction.")
        return
        
    reddit_count = 0
    youtube_count = 0
    topic_counts = Counter()
    social_skill_counts = Counter()
    
    broad_skills = ["python", "javascript", "react", "aws", "docker", "kubernetes", "typescript", "node", "sql", "ai", "machine learning"]

    for item in intel_data:
        source = item.get("source_type", "").lower()
        if source == "reddit": reddit_count += 1
        elif source == "youtube": youtube_count += 1
        
        text = str(item.get("content_summary", "")).lower()
        
        if "layoff" in text or "freeze" in text or "fired" in text: topic_counts["Layoffs & Freezes"] += 1
        if "offer" in text or "hired" in text or "passed" in text: topic_counts["Getting Hired"] += 1
        if "ai" in text or "chatgpt" in text or "replace" in text or "automation" in text: topic_counts["AI Taking Jobs"] += 1
        if "remote" in text or "wfh" in text or "office" in text: topic_counts["Remote Work"] += 1
        if "interview" in text or "leetcode" in text or "system design" in text: topic_counts["Interview Prep"] += 1
            
        for skill in broad_skills:
            if skill in text:
                social_skill_counts[skill] += 1
                
    # Normalize Heat Scores for Topics (1-100)
    max_topic_val = max(topic_counts.values()) if topic_counts else 1
    trending_topics = []
    for topic, count in topic_counts.most_common(5):
        heat_score = int((count / max_topic_val) * 100)
        trending_topics.append({"topic": topic, "heat_score": heat_score})

    # Algorithmic Market Mood
    mood = "The tech market is experiencing a standard calibration cycle with balanced discussions across topics."
    if trending_topics:
        top_topic = trending_topics[0]["topic"]
        if top_topic == "AI Taking Jobs":
            mood = "Algorithmic sentiment analysis indicates massive community anxiety surrounding AI automation and job displacement."
        elif top_topic == "Layoffs & Freezes":
            mood = "Leading indicators show a high degree of fear regarding ongoing layoffs and hiring freezes across the industry."
        elif top_topic == "Getting Hired":
            mood = "The market pulse shows strong optimism, with a high volume of positive hiring outcomes and offer discussions."
        elif top_topic == "Remote Work":
            mood = "The primary friction point in the market right now revolves around Return to Office (RTO) mandates vs Remote flexibility."

    # Construct the final JSON
    predictive_json = {
        "market_mood": mood,
        "trending_topics": trending_topics,
        "source_metrics": {
            "youtube": youtube_count,
            "reddit": reddit_count,
            "total": youtube_count + reddit_count
        }
    }
    
    final_json_string = json.dumps(predictive_json)
    
    if analytics_res.data:
        latest_id = analytics_res.data[0].get("id")
        if latest_id:
            supabase.table("analytics_insights").update({
                "ai_market_summary": final_json_string
            }).eq("id", latest_id).execute()
            logger.info("Successfully updated the frontend with Deterministic Algorithmic Predictions!")
    else:
        supabase.table("analytics_insights").insert({
            "ai_market_summary": final_json_string,
            "is_latest": True,
            "trending_skills": [],
            "trending_titles": [],
            "total_jobs_analyzed": 0
        }).execute()
        logger.info("Successfully created NEW Algorithmic Predictions!")

if __name__ == "__main__":
    run_predictive_engine()
