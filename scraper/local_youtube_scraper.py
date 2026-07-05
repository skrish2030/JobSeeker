import os
import logging
from dotenv import load_dotenv
from youtubesearchpython import VideosSearch
from youtube_transcript_api import YouTubeTranscriptApi
from supabase import create_client, Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("local_youtube")

def get_supabase() -> Client:
    load_dotenv()
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not key:
        raise ValueError("Please set SUPABASE_URL and SUPABASE_SERVICE_KEY in your local .env file")
    return create_client(url, key)

def fetch_youtube_intelligence():
    queries = ["tech job market 2024", "software engineering job market", "tech layoffs", "hiring trends programming"]
    raw_posts = []

    for query in queries:
        logger.info(f"Searching YouTube for: {query}")
        try:
            import urllib.request
            import urllib.parse
            import re
            
            search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
            req = urllib.request.Request(search_url, headers={'User-Agent': 'Mozilla/5.0'})
            html = urllib.request.urlopen(req).read().decode()
            
            # Extract video IDs
            video_ids = re.findall(r"watch\?v=(\S{11})", html)
            unique_ids = []
            for vid in video_ids:
                if vid not in unique_ids:
                    unique_ids.append(vid)
                    
            for video_id in unique_ids[:2]:
                title = f"YouTube Video: {query}" # Fallback title since we bypass API
                channel = "unknown"
                url = f"https://youtube.com/watch?v={video_id}"
                
                # Fetch transcript
                try:
                    ytt_api = YouTubeTranscriptApi()
                    transcript_list = ytt_api.list(video_id)
                    transcript = transcript_list.find_transcript(['en'])
                    transcript_data = transcript.fetch()
                    
                    # Join the first 100 lines to keep it manageable
                    text = " ".join([getattr(t, 'text', '') for t in transcript_data[:100]])
                except Exception as e:
                    logger.warning(f"Could not fetch transcript for {title}: {e}")
                    text = "No transcript available."
                    continue # Skip videos without transcripts

                raw_posts.append({
                    "source_type": "youtube",
                    "author": f"yt/{channel}",
                    "content_summary": title[:150], # title as short summary
                    "trending_skills_detected": [], # Daily AI will fill this conceptually
                    "sentiment": "Neutral",
                    "url": url,
                    # We store the raw text directly in content_summary for the AI to read later
                    # Actually, let's append it so the AI can read it from the database
                    "content_summary": f"Title: {title} | Transcript snippet: {text[:800]}..."
                })
                
                # Sleep to mimic human behavior and avoid IP blocks
                import time
                time.sleep(10)
        except Exception as e:
            logger.error(f"Failed searching {query}: {e}")

    return raw_posts

def run_local_youtube_scraper():
    logger.info("Starting local YouTube scraper...")
    supabase = get_supabase()
    
    posts = fetch_youtube_intelligence()
    if not posts:
        logger.warning("No YouTube data gathered.")
        return

    logger.info(f"Saving {len(posts)} YouTube videos to intelligence_feed...")
    for post in posts:
        try:
            supabase.table("intelligence_feed").insert(post).execute()
        except Exception as e:
            logger.error(f"Failed to insert post: {e}")

    logger.info("Local YouTube scraping complete! The daily Gemini AI will analyze this tonight.")

if __name__ == "__main__":
    run_local_youtube_scraper()
