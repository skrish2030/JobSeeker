import os
import sys
import re
import time
import urllib.parse
import xml.etree.ElementTree as ET
import requests
import json
import logging
from datetime import datetime

# Add project root to path to resolve backend/scraper imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import create_client, Client
from dotenv import load_dotenv

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] - %(message)s")
logger = logging.getLogger("market_intelligence_expanded")

# Target keywords to analyze
TECH_KEYWORDS = ["react", "node", "python", "aws", "typescript", "kubernetes", "ai", "llm", "rust", "golang", "devops", "cloud"]
POSITIVE_INDICATORS = ["hiring", "boom", "growth", "funding", "expanding", "rise", "success", "jobs"]
NEGATIVE_INDICATORS = ["layoff", "freeze", "downsize", "cut", "recession", "drop", "decline", "ghosting", "fired"]

def load_env_manually(filepath):
    """Fallback manual parser for .env files when python-dotenv is not installed."""
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip().strip('"').strip("'")
        except Exception as e:
            print(f"    [!] Failed to read {filepath} manually: {e}")

def get_supabase_client() -> Client:
    load_env_manually(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    load_env_manually(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend-next", ".env.local"))
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
        key = os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")
    if not url or not key:
        raise ValueError("Supabase keys not found.")
    return create_client(url, key)

def calculate_sentiment(text: str):
    text_lower = text.lower()
    pos = sum(1 for w in POSITIVE_INDICATORS if w in text_lower)
    neg = sum(1 for w in NEGATIVE_INDICATORS if w in text_lower)
    if pos > neg: return "Positive"
    if neg > pos: return "Negative"
    return "Neutral"

def detect_skills(text: str):
    text_lower = text.lower()
    return [skill for skill in TECH_KEYWORDS if skill in text_lower]

# 1. Google News RSS scraper (100% reliable, returns Google Search / news data)
def scrape_google_news(query="tech job market hiring"):
    logger.info(f"[*] Querying Google News RSS for: '{query}'...")
    encoded_query = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    
    insights = []
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            root = ET.fromstring(res.content)
            for item in root.findall(".//item")[:10]:
                title = item.find("title").text or ""
                link = item.find("link").text or ""
                pub_date = item.find("pubDate").text or ""
                source = item.find("source").text if item.find("source") is not None else "Google News"
                
                content_text = f"{title} (Published: {pub_date})"
                skills = detect_skills(content_text)
                sentiment = calculate_sentiment(content_text)
                
                insights.append({
                    "source_type": "google_news",
                    "author": source,
                    "content_summary": title[:200],
                    "trending_skills_detected": skills,
                    "sentiment": sentiment,
                    "url": link
                })
        else:
            logger.error(f"[-] Google News HTTP {res.status_code}")
    except Exception as e:
        logger.error(f"[-] Google News Scraper error: {e}")
    return insights

# 2. Tech Podcasts RSS scraper (Syntax.fm, Software Engineering Daily)
def scrape_podcasts():
    logger.info("[*] Querying Podcast RSS feeds...")
    feeds = [
        {"name": "Syntax.fm", "url": "https://feed.syntax.fm/"},
        {"name": "Software Engineering Daily", "url": "https://softwareengineeringdaily.com/feed/"}
    ]
    
    insights = []
    headers = {"User-Agent": "Mozilla/5.0"}
    for f in feeds:
        try:
            logger.info(f"  Fetching: {f['name']} feed...")
            res = requests.get(f["url"], headers=headers, timeout=10)
            if res.status_code == 200:
                root = ET.fromstring(res.content)
                for item in root.findall(".//item")[:5]:
                    title = item.find("title").text or ""
                    link = item.find("link").text or ""
                    desc_elem = item.find("description")
                    desc = desc_elem.text if desc_elem is not None else ""
                    if desc:
                        # Clean HTML tags from RSS descriptions
                        desc = re.sub('<[^<]+?>', '', desc)
                        
                    content_text = f"{title} {desc}"
                    skills = detect_skills(content_text)
                    sentiment = calculate_sentiment(content_text)
                    
                    insights.append({
                        "source_type": "podcast",
                        "author": f["name"],
                        "content_summary": title[:200],
                        "trending_skills_detected": skills,
                        "sentiment": sentiment,
                        "url": link
                    })
            else:
                logger.error(f"  [-] {f['name']} HTTP {res.status_code}")
        except Exception as e:
            logger.error(f"  [-] Failed to scrape podcast {f['name']}: {e}")
    return insights

# 3. YouTube Search Scraper (Stealthy page renderer parser)
def scrape_youtube(query="tech jobs hiring layoffs"):
    logger.info(f"[*] Querying YouTube Search for: '{query}'...")
    encoded_query = urllib.parse.quote(query)
    url = f"https://www.youtube.com/results?search_query={encoded_query}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    insights = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            # Extract the ytInitialData JSON object from page scripts
            match = re.search(r'var ytInitialData\s*=\s*({.*?});', res.text)
            if match:
                data = json.loads(match.group(1))
                
                # Dig down into the YouTube search results render structure
                contents = data.get("contents", {}).get("twoColumnSearchResultRenderer", {}).get("primaryContents", {}).get("sectionListRenderer", {}).get("contents", [])
                video_items = []
                for content in contents:
                    items = content.get("itemSectionRenderer", {}).get("contents", [])
                    for item in items:
                        if "videoRenderer" in item:
                            video_items.append(item["videoRenderer"])
                            
                # Process the top 10 search result videos
                for video in video_items[:10]:
                    title = video.get("title", {}).get("runs", [{}])[0].get("text", "")
                    video_id = video.get("videoId", "")
                    video_link = f"https://www.youtube.com/watch?v={video_id}"
                    channel_name = video.get("ownerText", {}).get("runs", [{}])[0].get("text", "Unknown Channel")
                    desc_runs = video.get("detailedMetadataSnippets", [{}])[0].get("snippetText", {}).get("runs", [])
                    desc = "".join(r.get("text", "") for r in desc_runs)
                    
                    content_text = f"{title} {desc}"
                    skills = detect_skills(content_text)
                    sentiment = calculate_sentiment(content_text)
                    
                    insights.append({
                        "source_type": "youtube",
                        "author": channel_name,
                        "content_summary": title[:200],
                        "trending_skills_detected": skills,
                        "sentiment": sentiment,
                        "url": video_link
                    })
            else:
                logger.warning("  [-] Failed to locate ytInitialData script in page HTML.")
        else:
            logger.error(f"  [-] YouTube search HTTP {res.status_code}")
    except Exception as e:
        logger.error(f"  [-] YouTube Scraper error: {e}")
    return insights

def run_expanded_intelligence():
    print("=" * 60)
    print("   JOBSEEKER MULTI-SOURCE MARKET INTELLIGENCE GATHERER")
    print("=" * 60)
    
    try:
        supabase = get_supabase_client()
        print("[+] Supabase connection successful.")
    except Exception as e:
        print(f"[-] Database connection failed: {e}")
        return

    # Gather data from all three expanded sources
    all_insights = []
    all_insights.extend(scrape_google_news())
    all_insights.extend(scrape_podcasts())
    all_insights.extend(scrape_youtube())
    
    if not all_insights:
        print("[-] No insights gathered from any source.")
        return

    print(f"\n[+] Total parsed insights gathered: {len(all_insights)}")
    print("[*] Ingesting parsed trends into Supabase 'intelligence_feed'...")
    
    inserted_count = 0
    for item in all_insights:
        try:
            # Upsert using url as a unique checker if supported, else simple insert
            supabase.table("intelligence_feed").insert(item).execute()
            inserted_count += 1
        except Exception as insert_err:
            # Skip duplicates/conflicts silently
            pass
            
    print("-" * 60)
    print(f"[+] Ingestion complete! Uploaded {inserted_count} new trends successfully.")
    print("=" * 60)

if __name__ == "__main__":
    run_expanded_intelligence()
