import sys
import re

filepath = r"C:\Users\skris\OneDrive\Desktop\JobSeeker\backend\scraper.py"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# I need to refactor the combination loop in `_execute_scraper_cycle_inner`.
# Old logic:
#     # Run scrape for combinations
#     for search_term in search_terms:
#         for location in locations:
#             logger.info(f"Scraping for: '{search_term}' in '{location}'...")
#             try:
#                 # Use parallel scraping instead of sequential to prevent timeouts
#                 df = scrape_jobs_parallel(
#                     site_names=site_names,
#                     search_term=search_term,
#                     location=location,
#                     results_wanted=100,
#                     hours_old=48, # only look at recent jobs
#                     country=country,
#                     linkedin_fetch_description=True # fetch description for classification
#                 )
#                 
#                 if df is None or df.empty:
#                     logger.info(f"No results found for '{search_term}' in '{location}'")
#                     continue

# I will replace this sequential nested loop with a ThreadPoolExecutor.

old_loop_pattern = r"    # Run scrape for combinations\n    for search_term in search_terms:\n        for location in locations:\n            logger\.info\(f\"Scraping for: '\{search_term\}' in '\{location\}'\.\.\.\"\)\n            try:\n                # Use parallel scraping instead of sequential to prevent timeouts\n                df = scrape_jobs_parallel\(\n                    site_names=site_names,\n                    search_term=search_term,\n                    location=location,\n                    results_wanted=100,\n                    hours_old=48, # only look at recent jobs\n                    country=country,\n                    linkedin_fetch_description=True # fetch description for classification\n                \)\n                \n                if df is None or df\.empty:\n                    logger\.info\(f\"No results found for '\{search_term\}' in '\{location\}'\"\)\n                    continue\n"

# The replacement logic:
new_loop_logic = """    # Run scrape for combinations concurrently (Partitioning search space)
    import itertools
    combinations = list(itertools.product(search_terms, locations))
    logger.info(f"Generated {len(combinations)} partitioned search chunks (terms x locations)")
    
    def process_partition(combo):
        search_term, location = combo
        logger.info(f"Scraping partition: '{search_term}' in '{location}'...")
        try:
            df = scrape_jobs_parallel(
                site_names=site_names,
                search_term=search_term,
                location=location,
                results_wanted=100,
                hours_old=48,
                country=country,
                linkedin_fetch_description=True
            )
            if df is None or df.empty:
                logger.info(f"No results found in partition '{search_term}' / '{location}'")
                return None
            return df
"""

# Now we need to append the rest of the loop block but indented for the function, 
# then execute the thread pool.
# We will use string manipulation to find the end of the loop body.

# It is easier to just replace the whole loop body. 
# But wait, what is after `continue` in the old logic? Let's check.
