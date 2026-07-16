import os

filepath = r"C:\Users\skris\OneDrive\Desktop\JobSeeker\backend\ai_engine.py"

new_code = """
def generate_market_insights_with_ai(job_stats, provider, model, api_key):
    prompt = f\"\"\"
You are a veteran recruiter and market analyst with over 30 years of experience in the tech industry. 
You are analyzing local database job demand statistics for a candidate.

Current Database Job Demand (Top titles and counts):
{job_stats}

Based on this real data and your immense market knowledge, please provide a highly authoritative, engaging analysis.
Your response must strictly be valid JSON with the following keys:
1. "booming_roles": A list of strings (3-5 items) naming the top roles that will boom in the next 5 years.
2. "best_certificates": A list of strings (3-5 items) naming the most valuable certifications (e.g., AWS Solutions Architect, CompTIA Security+).
3. "market_summary": A 3-4 sentence powerful summary of current hiring trends, advising the candidate on where to focus.
4. "youtube_queries": A list of exactly 3 highly specific YouTube search queries (strings) that the candidate should look up to learn more (e.g., "Best AWS certifications for beginners 2026").

Do not include any markdown formatting, only raw valid JSON.
\"\"\"
    data = call_ai_model(prompt, provider, model, api_key, expect_json=True)
    if data and isinstance(data, dict):
        return data
    return {
        "booming_roles": ["AI/ML Engineer", "Cloud Architect", "Cybersecurity Analyst"],
        "best_certificates": ["AWS Solutions Architect", "CompTIA Security+", "Google Cloud Professional"],
        "market_summary": "The tech market is aggressively shifting towards AI integration and Cloud Security. Focus on mastering Python and deploying secure cloud applications to remain highly competitive.",
        "youtube_queries": ["Top IT Certifications 2026", "Trending tech jobs", "AI Engineer career path"]
    }
"""

with open(filepath, "a", encoding="utf-8") as f:
    f.write("\n" + new_code)
print("Successfully appended generate_market_insights_with_ai to ai_engine.py")
