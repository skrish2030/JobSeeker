import os
import requests
import json
import logging
import google.generativeai as genai
from supabase import create_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("market_intelligence")

def get_reddit_posts(subreddit):
    headers = {'User-agent': 'JobSeeker Market Intelligence Bot 1.0'}
    try:
        url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=5"
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        data = res.json()
        posts = []
        for child in data.get('data', {}).get('children', []):
            post = child['data']
            # Skip pinned/stickied posts
            if post.get('stickied'):
                continue
            posts.append({
                'source_type': 'reddit',
                'author': f"r/{subreddit}",
                'title': post.get('title', ''),
                'text': post.get('selftext', '')[:1000], # limit text
                'url': f"https://reddit.com{post.get('permalink')}"
            })
        return posts
    except Exception as e:
        logger.error(f"Failed to fetch Reddit {subreddit}: {e}")
        return []

def extract_insights_with_gemini(raw_posts):
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        logger.error("GOOGLE_API_KEY not set")
        return []

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')

    prompt = f"""
    You are an expert tech career analyst. I am giving you a list of recent trending community posts from Reddit.
    Your goal is to analyze them and extract 'Market Intelligence' regarding software engineering, tech careers, and skills.
    
    Raw Posts Data:
    {json.dumps(raw_posts, indent=2)}

    For each post that is relevant to tech careers, skills, or hiring trends, generate a JSON object. 
    Ignore posts that are irrelevant (e.g., memes, unrelated questions).
    
    Output a JSON array of objects with this EXACT structure (no markdown blocks, just raw JSON):
    [
      {{
        "source_type": "reddit",
        "author": "r/...",
        "content_summary": "A 1-2 sentence summary of what this post indicates about the market/skills.",
        "trending_skills_detected": ["python", "react", "aws"], // Only include specific tech skills mentioned or implied
        "sentiment": "Positive", // Or "Negative", "Neutral"
        "url": "url from the raw data"
      }}
    ]
    """

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        
        return json.loads(text)
    except Exception as e:
        logger.error(f"Gemini Analysis failed: {e}")
        logger.error(f"Raw response: {response.text if 'response' in locals() else 'None'}")
        return []

def run_intelligence():
    # 1. Gather Raw Data
    logger.info("Gathering raw data from communities...")
    raw_posts = []
    for sub in ["cscareerquestions", "dataengineering", "artificial", "devops"]:
        raw_posts.extend(get_reddit_posts(sub))
    
    if not raw_posts:
        logger.warning("No raw data gathered.")
        return

    # 2. Analyze with AI
    logger.info("Analyzing trends with Gemini...")
    insights = extract_insights_with_gemini(raw_posts)

    if not insights:
        logger.warning("No insights extracted.")
        return

    # 3. Save to Supabase
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        logger.error("Missing Supabase credentials")
        return

    supabase = create_client(url, key)
    
    logger.info(f"Saving {len(insights)} insights to database...")
    for item in insights:
        try:
            supabase.table("intelligence_feed").insert(item).execute()
        except Exception as e:
            logger.error(f"Failed to insert insight: {e}")

    logger.info("Market Intelligence gathering complete!")

if __name__ == "__main__":
    run_intelligence()
