import os
import sys

# Add backend to path
sys.path.append("C:/Users/skris/OneDrive/Desktop/JobSeeker")

# Mock the context variables for user/profile
from backend.database import active_user_id_var, active_profile_id_var
u_tok = active_user_id_var.set("global")
p_tok = active_profile_id_var.set("default")

from backend.scraper import run_targeted_scrape

try:
    print("Running targeted scrape for Java...")
    res = run_targeted_scrape("Java", "")
    print(f"Success! Found and processed {len(res)} jobs.")
    for j in res:
         print(f"  - Title: {j.get('title')}, Company: {j.get('company')}, Score: {j.get('score')}")
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    active_user_id_var.reset(u_tok)
    active_profile_id_var.reset(p_tok)
