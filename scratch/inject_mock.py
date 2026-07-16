import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_SERVICE_KEY"))

supabase.table("intelligence_feed").insert([
    {"source_type": "youtube", "author": "yt/TechLead", "content_summary": "Title: Tech job market is collapsing 2026 | Transcript snippet: Nobody is hiring for basic React anymore. You need to know AWS, Docker, and lower level languages like C++. Im seeing a huge demand for AI integration engineers. Stop taking basic Udemy courses and build real projects.", "sentiment": "Neutral"},
    {"source_type": "reddit", "author": "r/cscareerquestions", "content_summary": "Just got 3 offers after 6 months of searching! The market is finally thawing. I focused heavily on Data Engineering and SQL. Avoid frontend, it is oversaturated.", "sentiment": "Positive"}
]).execute()
print("Injected mock data")
