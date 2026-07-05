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
            videos_search = VideosSearch(query, limit=2)
            results = videos_search.result()['result']
            
            for video in results:
                video_id = video['id']
                title = video.get('title', '')
                channel = video.get('channel', {}).get('name', 'Unknown')
                url = video.get('link', f"https://youtube.com/watch?v={video_id}")
                
                # Fetch transcript
                try:
                    transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
                    # Join the first 100 lines to keep it manageable
                    text = " ".join([t['text'] for t in transcript_list[:100]])
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
