import os

filepath = r"C:\Users\skris\OneDrive\Desktop\JobSeeker\backend\ai_engine.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# We need to replace the generate_market_insights_with_ai function if it exists.
start_marker = "def generate_market_insights_with_ai"

new_func = """def generate_market_insights_with_ai(job_stats, provider, model, api_key):
    prompt = f\"\"\"
You are a veteran recruiter and market analyst with over 30 years of experience in the tech industry. 
You are analyzing local database job demand statistics for a candidate.

Current Database Job Demand (Top titles and counts):
{job_stats}

Based on this real data and your immense market knowledge, please provide a highly authoritative, engaging analysis.
You MUST draw inspiration from top industry influencers such as NetworkChuck, freeCodeCamp, Mosh, MKBHD, and Dave2D.

Your response must strictly be valid JSON with the following keys:
1. "booming_roles": A list of strings (3-5 items) naming the top roles that will boom in the next 5 years (e.g. AI/ML Engineer, Cloud Architect).
2. "best_certificates": A list of strings (3-5 items) naming the most valuable certifications (e.g., AWS Solutions Architect, CompTIA Security+, CISSP).
3. "market_summary": A 3-4 sentence powerful summary of current hiring trends, advising the candidate on where to focus.
4. "youtube_queries": A list of exactly 3 highly specific YouTube search queries (strings) that the candidate should look up to learn more. Focus the queries on influencers like "NetworkChuck cybersecurity career", "freeCodeCamp full course", "AWS training roadmap".

Do not include any markdown formatting, only raw valid JSON.
\"\"\"
    data = call_ai_model(prompt, provider, model, api_key, expect_json=True)
    if data and isinstance(data, dict):
        return data
    return {
        "booming_roles": ["AI/ML Engineer", "Cloud Architect", "Cybersecurity Analyst"],
        "best_certificates": ["AWS Solutions Architect", "CompTIA Security+", "Google IT Support"],
        "market_summary": "The tech market is aggressively shifting towards AI integration and Cloud Security. Focus on mastering Python and deploying secure cloud applications to remain highly competitive.",
        "youtube_queries": ["NetworkChuck IT Career", "freeCodeCamp Python", "AWS Solutions Architect roadmap"]
    }
"""

if start_marker in content:
    content = content[:content.find(start_marker)] + new_func
else:
    content += "\n\n" + new_func

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated ai_engine.py with robust generate_market_insights_with_ai.")
