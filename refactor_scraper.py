import sys

filepath = r"C:\Users\skris\OneDrive\Desktop\JobSeeker\backend\scraper.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

old_block = """    # Run scrape for combinations
    for search_term in search_terms:
        for location in locations:
            logger.info(f"Scraping for: '{search_term}' in '{location}'...")
            try:
                # Use parallel scraping instead of sequential to prevent timeouts
                df = scrape_jobs_parallel(
                    site_names=site_names,
                    search_term=search_term,
                    location=location,
                    results_wanted=100,
                    hours_old=48, # only look at recent jobs
                    country=country,
                    linkedin_fetch_description=True # fetch description for classification
                )
                
                if df is None or df.empty:
                    logger.info(f"No results found for '{search_term}' in '{location}'")
                    continue
                    
                total_found += len(df)
                
                # Iterate over rows in the dataframe
                for _, row in df.iterrows():
                    # Handle flexible fields returned by jobspy
                    job_url = row.get("job_url") or row.get("job_url_direct") or ""
                    if not job_url:
                        continue
                        
                    # Format salary string
                    min_amt = row.get("min_amount")
                    max_amt = row.get("max_amount")
                    interval = row.get("interval")
                    salary_str = ""
                    if pd.notna(min_amt) and pd.notna(max_amt):
                        try:
                            salary_str = f"${int(min_amt):,}/yr - ${int(max_amt):,}/yr" if interval == "yearly" else f"${min_amt} - ${max_amt} per {interval}"
                        except Exception:
                            salary_str = f"${min_amt} - ${max_amt} per {interval}"
                    elif pd.notna(min_amt):
                        salary_str = f"${min_amt} per {interval}"
                    
                    company_portal_url = None
                    job_company_lower = (row.get("company") or "").lower().strip()
                    for tc in target_companies:
                        tc_name = tc.get("name", "") if isinstance(tc, dict) else tc
                        if tc_name.lower().strip() == job_company_lower:
                            company_portal_url = tc.get("portal_url") if isinstance(tc, dict) else None
                            break

                    job_data = {
                        "id": generate_job_id(row.get("company"), row.get("title"), row.get("location")),
                        "job_url": job_url,
                        "title": row.get("title") or "Untitled Role",
                        "company": row.get("company") or "Unknown Company",
                        "location": row.get("location") or location,
                        "source": row.get("site") or "job_board",
                        "posted_date": str(row.get("date_posted")) if row.get("date_posted") else datetime.today().strftime('%Y-%m-%d'),
                        "salary": salary_str,
                        "description": row.get("description") or "",
                        "company_portal_url": company_portal_url
                    }
                    
                    scraped_jobs_list.append(job_data)
                    
            except Exception as e:
                logger.error(f"Error scraping query '{search_term}' in '{location}': {str(e)}")
                # Continue other queries even if one fails
                continue"""

new_block = """    # Run scrape for combinations concurrently (Partitioning search space)
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
                return []
                
            local_scraped = []
            for _, row in df.iterrows():
                job_url = row.get("job_url") or row.get("job_url_direct") or ""
                if not job_url:
                    continue
                    
                min_amt = row.get("min_amount")
                max_amt = row.get("max_amount")
                interval = row.get("interval")
                salary_str = ""
                if pd.notna(min_amt) and pd.notna(max_amt):
                    try:
                        salary_str = f"${int(min_amt):,}/yr - ${int(max_amt):,}/yr" if interval == "yearly" else f"${min_amt} - ${max_amt} per {interval}"
                    except Exception:
                        salary_str = f"${min_amt} - ${max_amt} per {interval}"
                elif pd.notna(min_amt):
                    salary_str = f"${min_amt} per {interval}"
                
                company_portal_url = None
                job_company_lower = (row.get("company") or "").lower().strip()
                for tc in target_companies:
                    tc_name = tc.get("name", "") if isinstance(tc, dict) else tc
                    if tc_name.lower().strip() == job_company_lower:
                        company_portal_url = tc.get("portal_url") if isinstance(tc, dict) else None
                        break

                job_data = {
                    "id": generate_job_id(row.get("company"), row.get("title"), row.get("location")),
                    "job_url": job_url,
                    "title": row.get("title") or "Untitled Role",
                    "company": row.get("company") or "Unknown Company",
                    "location": row.get("location") or location,
                    "source": row.get("site") or "job_board",
                    "posted_date": str(row.get("date_posted")) if row.get("date_posted") else datetime.today().strftime('%Y-%m-%d'),
                    "salary": salary_str,
                    "description": row.get("description") or "",
                    "company_portal_url": company_portal_url
                }
                local_scraped.append(job_data)
            return local_scraped
        except Exception as e:
            logger.error(f"Error scraping partition '{search_term}' in '{location}': {str(e)}")
            return []

    # Execute partitions concurrently
    # Limit max_workers to avoid hammering job boards and triggering immediate IP bans
    with ThreadPoolExecutor(max_workers=min(5, len(combinations))) as partition_executor:
        futures = {partition_executor.submit(process_partition, combo): combo for combo in combinations}
        for future in as_completed(futures, timeout=120):
            try:
                res = future.result()
                if res:
                    scraped_jobs_list.extend(res)
                    total_found += len(res)
            except TimeoutError:
                logger.warning("Partition scrape timed out.")
            except Exception as e:
                logger.error(f"Partition scrape failed: {e}")"""

if old_block in content:
    content = content.replace(old_block, new_block)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print("Successfully refactored scraper.py for partitioned search.")
else:
    print("Could not find old_block in scraper.py!")
    sys.exit(1)
