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

def extract_insights_locally(raw_posts):
    """Fallback heuristics to extract skills and sentiment if Gemini fails or is missing."""
    logger.info("Using local heuristics for Market Intelligence (Gemini unavailable)...")
    insights = []
    
    # Broader range of skills across different industries
    broad_skills = ["python", "react", "excel", "sql", "salesforce", "marketing", "management", "leadership", "aws", "data analysis", "design", "agile", "scrum", "finance", "communication"]
    
    # Basic sentiment keywords
    positive_words = ["offer", "hired", "accept", "success", "growth", "learning", "passed"]
    negative_words = ["layoff", "laid off", "reject", "ghosted", "tough", "bad", "rescinded", "freeze", "unemployed"]
    
    for post in raw_posts:
        text = (post.get('title', '') + " " + post.get('text', '')).lower()
        
        # Detect skills
        detected_skills = [skill for skill in broad_skills if skill in text]
        
        # Only include posts that actually mention skills or career keywords
        if not detected_skills and not any(w in text for w in positive_words + negative_words):
            continue
            
        # Determine sentiment
        pos_count = sum(1 for w in positive_words if w in text)
        neg_count = sum(1 for w in negative_words if w in text)
        
        sentiment = "Neutral"
        if pos_count > neg_count:
            sentiment = "Positive"
        elif neg_count > pos_count:
            sentiment = "Negative"
            
        insights.append({
            "source_type": post['source_type'],
            "author": post['author'],
            "content_summary": post['title'][:150] + "...", 
            "trending_skills_detected": detected_skills,
            "sentiment": sentiment,
            "url": post['url']
        })
        
    return insights[:20]

def extract_insights_with_gemini(raw_posts):
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        logger.warning("GOOGLE_API_KEY not set, falling back to local heuristics.")
        return extract_insights_locally(raw_posts)

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')

    prompt = f"""
    You are a Chief Market Strategist and Senior Executive Recruiter with 30+ years of industry experience. Your ultimate goal is to support candidates end-to-end: to alert them to what the world thinks, which skills are hot right now, what they need to learn, which certificates are best, and when they should consider pivoting their career to achieve their goals. Think logically, be incredibly smart, and do not waste tokens.
    
    Analyze these recent community discussions to extract actionable 'Market Intelligence' regarding jobs, hiring trends, and skills.
    
    Raw Posts Data:
    {json.dumps(raw_posts, indent=2)}

    For each post that is relevant to careers, skills, or hiring trends, generate a JSON object. 
    Ignore posts that are irrelevant (e.g., memes, unrelated questions).
    
    Output a JSON array of objects with this EXACT structure (no markdown blocks, just raw JSON):
    [
      {{
        "source_type": "reddit",
        "author": "r/...",
        "content_summary": "A 2-3 sentence strategic analysis. Do NOT just summarize the post. Instead, act as a mentor: alert the user to the trend, tell them exactly what skills/certificates to learn based on this, and advise them if this means they should switch careers or double down.",
        "trending_skills_detected": ["excel", "project management", "python", "AWS Certified Solutions Architect"], // Extract ANY professional skill or certificate mentioned
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
        return extract_insights_locally(raw_posts)

def run_intelligence():
    # 1. Gather Raw Data across broad career subreddits
    logger.info("Gathering raw data from communities...")
    raw_posts = []
    # Broadened subreddits to capture all roles, not just software
    for sub in ["jobs", "careerguidance", "recruitinghell", "cscareerquestions", "marketing", "FinancialCareers"]:
        raw_posts.extend(get_reddit_posts(sub))
    
    if not raw_posts:
        logger.warning("No raw data gathered.")
        return

    # 2. Analyze locally (AI disabled per user request)
    logger.info("Analyzing trends locally (AI disabled)...")
    insights = extract_insights_locally(raw_posts)

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
