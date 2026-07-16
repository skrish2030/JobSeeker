import os

filepath = r"C:\Users\skris\OneDrive\Desktop\JobSeeker\backend\main.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

new_route = """
# --- Market Analyst Insights Endpoint ---
@app.get("/api/market-insights")
def api_get_market_insights():
    try:
        from backend.database import db, get_all_settings
        from backend.ai_engine import generate_market_insights_with_ai
        
        # 1. Aggregate top 5 job titles from local database
        pipeline = [
            {"$group": {"_id": "$title", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]
        top_jobs = list(db.jobs.aggregate(pipeline))
        job_stats = "\\n".join([f"- {job['_id']}: {job['count']} jobs" for job in top_jobs])
        if not job_stats:
            job_stats = "No jobs found in database yet. Assume general software engineering market."
            
        # 2. Call AI
        settings = get_all_settings()
        ai_provider = settings.get("ai_provider", "gemini")
        ai_model = settings.get("ai_model", "gemini-2.0-flash")
        ai_api_key = settings.get("ai_api_key", "")
        
        ai_response = generate_market_insights_with_ai(job_stats, ai_provider, ai_model, ai_api_key)
        
        # 3. Fetch YouTube Videos
        youtube_videos = []
        try:
            from youtubesearchpython import VideosSearch
            for query in ai_response.get("youtube_queries", []):
                videosSearch = VideosSearch(query, limit = 1)
                res = videosSearch.result()
                if res and res.get("result"):
                    vid = res["result"][0]
                    youtube_videos.append({
                        "title": vid.get("title"),
                        "link": vid.get("link"),
                        "thumbnail": vid.get("thumbnails", [{}])[0].get("url"),
                        "channel": vid.get("channel", {}).get("name")
                    })
        except Exception as e:
            logger.error(f"Failed to fetch YouTube videos: {e}")
            
        return {
            "status": "success",
            "stats": top_jobs,
            "analysis": ai_response,
            "videos": youtube_videos
        }
    except Exception as e:
        logger.error(f"Market Insights Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
"""

if "/api/market-insights" not in content:
    with open(filepath, "a", encoding="utf-8") as f:
        f.write("\n" + new_route)
    print("Appended /api/market-insights to main.py")
else:
    print("Route already exists in main.py")
