import os
import logging
from collections import Counter
import json
from supabase import create_client, Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("analytics_engine")

def get_supabase() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
    return create_client(url, key)

def run_analytics():
    supabase = get_supabase()
    
    # 1. Fetch latest 1,000 jobs
    logger.info("Fetching latest 1,000 jobs for analytics...")
    response = supabase.table("jobs").select("title, description, location").order("scraped_at", desc=True).limit(1000).execute()
    jobs = response.data
    
    if not jobs:
        logger.warning("No jobs found in database to analyze.")
        return
        
    logger.info(f"Analyzing {len(jobs)} jobs...")
    
    # 2. Local Smart Logic: Trending Titles
    titles = [j.get("title", "") for j in jobs if j.get("title")]
    # Normalize titles slightly
    normalized_titles = []
    for t in titles:
        t_low = t.lower()
        if "software engineer" in t_low or "swe" in t_low:
            normalized_titles.append("Software Engineer")
        elif "frontend" in t_low or "front end" in t_low:
            normalized_titles.append("Frontend Developer")
        elif "backend" in t_low or "back end" in t_low:
            normalized_titles.append("Backend Developer")
        elif "full stack" in t_low or "fullstack" in t_low:
            normalized_titles.append("Full Stack Developer")
        elif "data" in t_low and "engineer" in t_low:
            normalized_titles.append("Data Engineer")
        elif "devops" in t_low or "sre" in t_low or "site reliability" in t_low:
            normalized_titles.append("DevOps Engineer")
        else:
            normalized_titles.append(t.title())
            
    top_titles = Counter(normalized_titles).most_common(10)
    trending_titles = [{"title": k, "count": v} for k, v in top_titles]
    
    # 3. Local Smart Logic: Trending Skills
    skill_keywords = [
        "Python", "JavaScript", "TypeScript", "React", "Node.js", "Java", "C++", 
        "C#", "Go", "Ruby", "AWS", "Azure", "GCP", "Docker", "Kubernetes", "SQL", 
        "PostgreSQL", "MongoDB", "Redis", "GraphQL", "REST API", "Next.js", "Tailwind"
    ]
    
    skill_counts = Counter()
    for j in jobs:
        desc = j.get("description", "").lower()
        for skill in skill_keywords:
            if skill.lower() in desc:
                skill_counts[skill] += 1
                
    top_skills = skill_counts.most_common(15)
    trending_skills = [{"skill": k, "count": v} for k, v in top_skills]
    
    # 4. Generate Local Market Summary
    top_skill_names = [s["skill"] for s in trending_skills[:3]]
    top_title_names = [t["title"] for t in trending_titles[:2]]
    
    ai_summary = (
        f"Based on our local analysis of {len(jobs)} recent job postings, the most sought-after roles currently are "
        f"{' and '.join(top_title_names)}. Employers are aggressively prioritizing candidates with proficiency in "
        f"{', '.join(top_skill_names)}. The market continues to heavily favor modern cloud-native tech stacks and robust engineering fundamentals."
    )

    # 5. Insert into Supabase
    # First, mark old insights as not latest
    supabase.table("analytics_insights").update({"is_latest": False}).eq("is_latest", True).execute()
    
    # Insert new insight
    logger.info("Saving new Analytics Insights to database...")
    supabase.table("analytics_insights").insert({
        "total_jobs_analyzed": len(jobs),
        "trending_skills": trending_skills,
        "trending_titles": trending_titles,
        "ai_market_summary": ai_summary,
        "is_latest": True
    }).execute()
    
    logger.info("Analytics Engine cycle complete.")

if __name__ == "__main__":
    run_analytics()
