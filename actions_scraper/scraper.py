import re
import hashlib
import pandas as pd
import logging
from datetime import datetime
from jobspy import scrape_jobs
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError

from actions_scraper.database import (
    get_all_settings,
    get_target_companies,
    save_jobs,
    log_scrape_run,
    update_scrape_run,
    generate_job_id,
    IS_LAMBDA,
    active_user_id_var,
    active_profile_id_var,
    get_job_by_id
)
from actions_scraper.ai_engine import process_job_classification
from actions_scraper.ats_scraper import scrape_all_company_portals

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scraper")

_scrape_in_progress = False

def scrape_jobs_parallel(site_names, search_term, location, results_wanted, hours_old, country, linkedin_fetch_description):
    """Runs JobSpy scrape_jobs for each site in site_names in parallel using ThreadPoolExecutor."""
    dfs = []
    
    def scrape_single_site(site):
        logger.info(f"Starting parallel board scrape for site '{site}' (term: '{search_term}', loc: '{location}')...")
        try:
            df = scrape_jobs(
                site_name=[site],
                search_term=search_term,
                location=location,
                results_wanted=results_wanted,
                hours_old=hours_old,
                country_indeed=country.lower() if country else "usa",
                linkedin_fetch_description=linkedin_fetch_description if site == "linkedin" else False
            )
            if df is not None and not df.empty:
                logger.info(f"Board scrape for site '{site}' finished: found {len(df)} jobs.")
                return df
            else:
                logger.info(f"Board scrape for site '{site}' finished: no jobs found.")
        except Exception as e:
            logger.error(f"Error scraping site '{site}': {str(e)}")
        return None

    # Run in parallel
    max_workers = len(site_names)
    executor = ThreadPoolExecutor(max_workers=max_workers)
    futures = {executor.submit(scrape_single_site, site): site for site in site_names}
    try:
        for future in as_completed(futures, timeout=18):
            df = future.result()
            if df is not None:
                dfs.append(df)
    except TimeoutError:
        logger.warning("Parallel board scrape hit 18-second timeout limit. Returning partial results.")
    finally:
        executor.shutdown(wait=False)
                
    if not dfs:
        return pd.DataFrame()
        
    try:
        combined_df = pd.concat(dfs, ignore_index=True)
        return combined_df
    except Exception as e:
        logger.error(f"Failed to concatenate scraped dataframes: {str(e)}")
        return pd.DataFrame()


def is_scrape_in_progress():
    global _scrape_in_progress
    return _scrape_in_progress

# generate_job_id helper is now imported from actions_scraper.database

def detect_country_from_location(location_str: str, default_country: str) -> str:
    """
    Detects the country from the user's location input string.
    If the location is empty, returns the default_country.
    Maps common country indicators, cities, provinces/states.
    Avoids 2-letter state collisions when default_country is USA.
    """
    if not location_str:
        return default_country

    loc = location_str.lower().strip()

    # Define detection rules for other countries (non-USA)
    # Check for full names and major unique cities/states/regions first
    country_rules = [
        ("Germany", ["germany", "deutschland", "berlin", "munich", "münchen", "frankfurt", "hamburg", "cologne", "köln", "stuttgart", "düsseldorf", "dusseldorf"]),
        ("Canada", ["canada", "toronto", "vancouver", "montreal", "calgary", "ottawa", "edmonton", "winnipeg", "ontario", "quebec", "british columbia", "alberta", "saskatchewan", "manitoba"]),
        ("UK", ["united kingdom", "great britain", "england", "scotland", "wales", "northern ireland", "london", "manchester", "birmingham", "leeds", "glasgow", "edinburgh", "liverpool", "bristol", "sheffield"]),
        ("India", ["india", "bengaluru", "bangalore", "mumbai", "delhi", "new delhi", "hyderabad", "pune", "chennai", "kolkata", "noida", "gurgaon", "gurugram"]),
        ("Australia", ["australia", "sydney", "melbourne", "brisbane", "perth", "adelaide"])
    ]

    for country_name, indicators in country_rules:
        for indicator in indicators:
            if re.search(r'\b' + re.escape(indicator) + r'\b', loc):
                return country_name

    # Check for USA-specific indicators
    usa_indicators = [
        "usa", "united states", "america", "united states of america",
        "chicago", "new york", "san francisco", "los angeles", "boston", "seattle", "austin", "atlanta", "dallas", "denver"
    ]
    us_states_full = [
        "alabama", "alaska", "arizona", "arkansas", "california", "colorado", "connecticut", "delaware", "florida", "georgia", "hawaii", "idaho", "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana", "maine", "maryland", "massachusetts", "michigan", "minnesota", "mississippi", "missouri", "montana", "nebraska", "nevada", "new hampshire", "new jersey", "new mexico", "new york", "north carolina", "north dakota", "ohio", "oklahoma", "oregon", "pennsylvania", "rhode island", "south carolina", "south dakota", "tennessee", "texas", "utah", "vermont", "virginia", "washington", "west virginia", "wisconsin", "wyoming"
    ]

    for indicator in usa_indicators + us_states_full:
        if re.search(r'\b' + re.escape(indicator) + r'\b', loc):
            return "USA"

    # US State 2-letter codes. Checked only if default country is USA to avoid collision.
    us_state_codes = [
        "al", "ak", "az", "ar", "ca", "co", "ct", "de", "fl", "ga", "hi", "id", "il", "in", "ia", "ks", "ky", "la", "me", "md", "ma", "mi", "mn", "ms", "mo", "mt", "ne", "nv", "nh", "nj", "nm", "ny", "nc", "nd", "oh", "ok", "or", "pa", "ri", "sc", "sd", "tn", "tx", "ut", "vt", "va", "wa", "wv", "wi", "wy"
    ]
    if any(re.search(r'\b' + re.escape(code) + r'\b', loc) for code in us_state_codes):
        if default_country.upper() in ["USA", "US", "UNITED STATES"]:
            return "USA"

    return default_country

def is_job_in_target_country(location_str: str, target_country: str) -> bool:
    """
    Filters out jobs that are not located in the target country.
    E.g. if target_country is USA, filters out jobs in Canada, Germany, etc.
    Avoids 2-letter state code collisions (like CA, DE, IN) by using unambiguous indicators.
    """
    if not location_str or (isinstance(location_str, float) and str(location_str).lower() == 'nan'):
        return True

    loc = str(location_str).lower().strip()
    country = str(target_country).lower().strip()

    # Resolve target country to canonical forms
    canonical_target = "usa"
    if country in ["usa", "us", "united states", "united states of america"]:
        canonical_target = "usa"
    elif country in ["canada", "ca"]:
        canonical_target = "canada"
    elif country in ["germany", "deutschland", "de"]:
        canonical_target = "germany"
    elif country in ["united kingdom", "uk", "gb", "great britain", "england"]:
        canonical_target = "uk"
    elif country in ["india", "in"]:
        canonical_target = "india"
    elif country in ["australia", "au"]:
        canonical_target = "australia"
    else:
        # Unknown country, don't filter to avoid blocking valid jobs
        return True

    # Indicators mapping for countries we want to distinguish
    country_indicators = {
        "usa": {
            "names": ["usa", "united states", "america", "united states of america"],
            "cities": ["chicago", "new york", "san francisco", "los angeles", "boston", "seattle", "austin", "atlanta", "dallas", "denver"],
            "regions": ["alabama", "alaska", "arizona", "arkansas", "california", "colorado", "connecticut", "delaware", "florida", "georgia", "hawaii", "idaho", "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana", "maine", "maryland", "massachusetts", "michigan", "minnesota", "mississippi", "missouri", "montana", "nebraska", "nv", "new hampshire", "new jersey", "new mexico", "new york", "north carolina", "north dakota", "ohio", "oklahoma", "oregon", "pennsylvania", "rhode island", "south carolina", "south dakota", "tennessee", "texas", "utah", "vermont", "virginia", "washington", "west virginia", "wisconsin", "wyoming"]
        },
        "canada": {
            "names": ["canada"],
            "cities": ["toronto", "vancouver", "montreal", "calgary", "ottawa", "edmonton", "mississauga", "winnipeg"],
            "regions": ["ontario", "quebec", "british columbia", "alberta", "saskatchewan", "manitoba", "nova scotia", "new brunswick", "newfoundland", "yukon", "nunavut"]
        },
        "germany": {
            "names": ["germany", "deutschland"],
            "cities": ["berlin", "munich", "münchen", "frankfurt", "hamburg", "cologne", "köln", "stuttgart", "düsseldorf", "dusseldorf"],
            "regions": ["bayern", "bavaria", "hessen", "saxony", "brandenburg"]
        },
        "uk": {
            "names": ["united kingdom", "uk", "england", "scotland", "wales", "northern ireland", "great britain"],
            "cities": ["london", "manchester", "birmingham", "leeds", "glasgow", "edinburgh", "liverpool", "bristol", "sheffield"]
        },
        "india": {
            "names": ["india"],
            "cities": ["bengaluru", "bangalore", "mumbai", "delhi", "new delhi", "hyderabad", "pune", "chennai", "kolkata", "noida", "gurgaon", "gurugram"]
        },
        "australia": {
            "names": ["australia"],
            "cities": ["sydney", "melbourne", "brisbane", "perth", "adelaide"],
            "regions": ["queensland", "victoria", "tasmania"]
        }
    }

    # Build negative indicators (blacklist) of other countries.
    # Exclude any 2-letter indicators from blacklist to avoid state code collisions.
    other_indicators = []
    for c_key, c_val in country_indicators.items():
        if c_key != canonical_target:
            all_items = c_val.get("names", []) + c_val.get("cities", []) + c_val.get("regions", [])
            for item in all_items:
                if len(item) > 2:
                    other_indicators.append(item)

    # If the location matches a blacklist indicator:
    # Check if it also matches target country indicators.
    # If not, filter it out.
    for indicator in other_indicators:
        if re.search(r'\b' + re.escape(indicator) + r'\b', loc):
            # Check for any positive indicators of the target country
            target_info = country_indicators[canonical_target]
            target_all = target_info.get("names", []) + target_info.get("cities", []) + target_info.get("regions", [])
            
            # For USA, we can check 2-letter state codes as positive indicators
            if canonical_target == "usa":
                us_states_short = ["al", "ak", "az", "ar", "ca", "co", "ct", "de", "fl", "ga", "hi", "id", "il", "in", "ia", "ks", "ky", "la", "me", "md", "ma", "mi", "mn", "ms", "mo", "mt", "ne", "nv", "nh", "nj", "nm", "ny", "nc", "nd", "oh", "ok", "or", "pa", "ri", "sc", "sd", "tn", "tx", "ut", "vt", "va", "wa", "wv", "wi", "wy"]
                target_all.extend(us_states_short)
                
            has_target = False
            for tn in target_all:
                if re.search(r'\b' + re.escape(tn) + r'\b', loc):
                    has_target = True
                    break
            if not has_target:
                return False

    # Also: if target is NOT USA, block it if it has strong USA indicators and no target country indicators.
    if canonical_target != "usa":
        usa_info = country_indicators["usa"]
        usa_all = usa_info.get("names", []) + usa_info.get("cities", []) + usa_info.get("regions", [])
        # Include US state codes
        us_states_short = ["al", "ak", "az", "ar", "ca", "co", "ct", "de", "fl", "ga", "hi", "id", "il", "in", "ia", "ks", "ky", "la", "me", "md", "ma", "mi", "mn", "ms", "mo", "mt", "ne", "nv", "nh", "nj", "nm", "ny", "nc", "nd", "oh", "ok", "or", "pa", "ri", "sc", "sd", "tn", "tx", "ut", "vt", "va", "wa", "wv", "wi", "wy"]
        usa_all.extend(us_states_short)

        for indicator in usa_all:
            if re.search(r'\b' + re.escape(indicator) + r'\b', loc):
                # Check for target country indicators
                target_info = country_indicators[canonical_target]
                target_all = target_info.get("names", []) + target_info.get("cities", []) + target_info.get("regions", [])
                has_target = False
                for tn in target_all:
                    if re.search(r'\b' + re.escape(tn) + r'\b', loc):
                        has_target = True
                        break
                if not has_target:
                    return False

    return True

def _execute_scraper_cycle_inner():
    """
    Retrieves settings from DB, initiates JobSpy scraper for each search term + location combination,
    classifies jobs, saves them to DB, and logs the execution metrics.
    """
    settings = get_all_settings()
    
    search_terms_str = settings.get("search_terms")
    if search_terms_str is None or search_terms_str.strip() == "":
        search_terms = [""]
    else:
        search_terms = [t.strip() for t in search_terms_str.split(",") if t.strip()]
        if not search_terms:
            search_terms = [""]
        
    locations_str = settings.get("locations") or "Remote"
    boards_str = settings.get("job_boards") or "linkedin,indeed"
    country = settings.get("scrape_country") or "USA"
    
    locations = [l.strip() for l in locations_str.split(",") if l.strip()]
    if not locations:
        locations = ["Remote"]
        
    site_names = [s.strip() for s in boards_str.split(",") if s.strip()]
    if not site_names:
        site_names = ["linkedin", "indeed"]
    
    target_companies = get_target_companies()
    
    total_found = 0
    total_new = 0
    
    scraped_jobs_list = []
    
    # Run scrape for combinations concurrently (Partitioning search space)
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
                results_wanted=2000,
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
                raw_comp = row.get("company")
                job_company_lower = (str(raw_comp) if pd.notna(raw_comp) else "").lower().strip()
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
                logger.error(f"Partition scrape failed: {e}")

    # Scrape directly from corporate portals for Target Companies in slow and steady batches
    if target_companies:
        try:
            # Optimize: Only check companies with non-empty portal URLs to avoid massive timeout overhead
            valid_companies = [c for c in target_companies if c.get("portal_url")]
            if valid_companies:
                # Sort stable
                valid_companies.sort(key=lambda x: x.get("name", "").lower())
                
                import math
                from actions_scraper.database import update_settings
                
                # Fetch cursor index
                cursor_str = settings.get("last_scraped_company_index") or "0"
                try:
                    last_idx = int(cursor_str)
                except ValueError:
                    last_idx = 0
                
                # Slices sized based on 48 cycles per day (calculated as ceil(total_companies / 48))
                # with a minimum batch size of 25 to ensure steady progress
                batch_size = max(25, int(math.ceil(len(valid_companies) / 48.0)))
                
                start_idx = last_idx % len(valid_companies)
                end_idx = start_idx + batch_size
                
                if end_idx > len(valid_companies):
                    batch = valid_companies[start_idx:] + valid_companies[:end_idx - len(valid_companies)]
                else:
                    batch = valid_companies[start_idx:end_idx]
                
                logger.info(f"Initiating corporate portal scrape batch for {len(batch)} companies (index {start_idx} to {end_idx - 1} of {len(valid_companies)} total)...")
                
                portal_jobs = scrape_all_company_portals(batch, search_terms_str)
                scraped_jobs_list.extend(portal_jobs)
                total_found += len(portal_jobs)
                
                # Save new index
                new_idx = (start_idx + len(batch)) % len(valid_companies)
                update_settings({"last_scraped_company_index": str(new_idx)})
            else:
                logger.info("No target companies have portal URLs configured. Skipping portal scrape.")
        except Exception as e:
            logger.error(f"Failed to scrape corporate portals: {str(e)}")

    # De-duplicate queries within the current scrape list based on job_url and filter by target country
    unique_scraped = {}
    for job in scraped_jobs_list:
        if not is_job_in_target_country(job.get("location"), country):
            logger.info(f"Filtering out job outside target country ({country}): {job['title']} at {job['company']} (Location: {job['location']})")
            continue
            
        # Append URLs to description if not already present
        desc = job.get("description") or ""
        job_url = job.get("job_url")
        company_portal_url = job.get("company_portal_url")
        url_notes = []
        if job_url and f"Source Job Link: {job_url}" not in desc:
            url_notes.append(f"Source Job Link: {job_url}")
        if company_portal_url and f"Company Career Portal: {company_portal_url}" not in desc:
            url_notes.append(f"Company Career Portal: {company_portal_url}")
        if url_notes:
            job["description"] = desc + "\n\n---\n" + "\n".join(url_notes)
            
        unique_scraped[job["job_url"]] = job
        
    jobs_list = list(unique_scraped.values())
    return total_found, jobs_list

def _execute_scraper_cycle():
    run_id = log_scrape_run(jobs_found=0, new_jobs=0, status="running")
    total_found = 0
    raw_jobs = []
    try:
        total_found, raw_jobs = _execute_scraper_cycle_inner()
        if raw_jobs:
            try:
                from actions_scraper.database import save_raw_jobs
                total_new = save_raw_jobs(raw_jobs)
                logger.info(f"Scrape cycle complete. Found {total_found} total, saved {total_new} raw staging jobs.")
                update_scrape_run(run_id, jobs_found=total_found, new_jobs=total_new, status="success")
            except Exception as e:
                logger.error(f"Error saving raw jobs to database: {str(e)}")
                update_scrape_run(run_id, jobs_found=total_found, new_jobs=0, status="failed", error_message=str(e))
        else:
            logger.info("Scrape cycle complete. No jobs to save.")
            update_scrape_run(run_id, jobs_found=total_found, new_jobs=0, status="success")
        return total_found, raw_jobs
    except Exception as e:
        logger.error(f"General scraper failure: {str(e)}")
        update_scrape_run(run_id, jobs_found=total_found, new_jobs=0, status="failed", error_message=str(e))
        raise e

def run_scraper_cycle():
    global _scrape_in_progress
    if _scrape_in_progress:
        logger.info("Scraper cycle already in progress. Skipping duplicate call.")
        return 0, 0
    _scrape_in_progress = True
    
    from actions_scraper.database import get_all_users_profiles
    
    try:
        profiles = get_all_users_profiles()
    except Exception as e:
        logger.error(f"Failed to fetch profiles for scraper run: {e}")
        _scrape_in_progress = False
        return 0, 0
        
    logger.info(f"Starting scraper cycle for {len(profiles)} user profiles...")
    
    total_found = 0
    total_new = 0
    
    try:
        for p in profiles:
            user_id = p['user_id']
            profile_id = p['id']
            logger.info(f"Executing scraper cycle for user profile: '{p['name']}' (User ID: {user_id}, Profile ID: {profile_id})...")
            
            user_token = active_user_id_var.set(user_id)
            profile_token = active_profile_id_var.set(profile_id)
            try:
                found, jobs_list = _execute_scraper_cycle()
                total_found += found
                total_new += len(jobs_list)
                
                # Immediately process unprocessed raw jobs for this user context
                process_raw_jobs_batch()
            except Exception as e:
                logger.error(f"Failed scraper cycle for profile '{p['name']}': {str(e)}")
            finally:
                active_user_id_var.reset(user_token)
                active_profile_id_var.reset(profile_token)
    finally:
        _scrape_in_progress = False
        
    return total_found, total_new

def run_targeted_scrape(search_term: str, location: str):
    """
    Runs JobSpy scraper synchronously for a single search term + location combination,
    checks corporate portals, classifies found jobs, and saves them to the DB.
    If location is empty, falls back to the default locations and country in settings.
    """
    search_term = search_term.strip()
    location = location.strip()
    logger.info(f"Starting on-demand targeted scrape for: '{search_term}' in '{location}'...")
    settings = get_all_settings()
    
    boards_str = settings.get("job_boards") or "linkedin,indeed"
    site_names = [s.strip() for s in boards_str.split(",") if s.strip()]
    if not site_names:
        site_names = ["linkedin", "indeed"]
        
    target_companies = get_target_companies()
    
    scraped_jobs_list = []
    total_found = 0
    total_new = 0
    
    if not location:
        locations = [""]
        country = settings.get("scrape_country") or "USA"
        logger.info(f"Empty location provided. Scraping without location constraint for country: {country}")
    else:
        locations = [location]
        default_country = settings.get("scrape_country") or "USA"
        country = detect_country_from_location(location, default_country)
        logger.info(f"Specific location provided: '{location}'. Detected target country: '{country}'")

    for loc in locations:
        logger.info(f"Scraping for: '{search_term}' in '{loc}' (indeed country: '{country}')...")
        try:
            df = scrape_jobs_parallel(
                site_names=site_names,
                search_term=search_term,
                location=loc,
                results_wanted=2000,
                hours_old=72,
                country=country,
                linkedin_fetch_description=True
            )
            
            if df is not None and not df.empty:
                total_found += len(df)
                
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
                    raw_comp = row.get("company")
                    job_company_lower = (str(raw_comp) if pd.notna(raw_comp) else "").lower().strip()
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
                        "location": row.get("location") or loc,
                        "source": row.get("site") or "job_board",
                        "posted_date": str(row.get("date_posted")) if row.get("date_posted") else datetime.today().strftime('%Y-%m-%d'),
                        "salary": salary_str,
                        "description": row.get("description") or "",
                        "company_portal_url": company_portal_url
                    }
                    
                    scraped_jobs_list.append(job_data)
        except Exception as e:
            logger.error(f"Error during targeted scrape for query '{search_term}' in '{loc}': {str(e)}")

    # Check direct corporate portals only if the search term matches a target company name
    # to avoid timeout during synchronous scraping of all 600+ companies.
    matching_companies = []
    search_term_lower = search_term.lower().strip()
    for tc in target_companies:
        tc_name = tc.get("name", "") if isinstance(tc, dict) else tc
        if tc_name.lower().strip() in search_term_lower or search_term_lower in tc_name.lower().strip():
            matching_companies.append(tc)

    if matching_companies:
        try:
            logger.info(f"Initiating corporate portal scrape for matching companies: {[c.get('name') if isinstance(c, dict) else c for c in matching_companies]}...")
            portal_jobs = scrape_all_company_portals(matching_companies, search_term)
            scraped_jobs_list.extend(portal_jobs)
            total_found += len(portal_jobs)
        except Exception as e:
            logger.error(f"Failed to scrape corporate portals: {str(e)}")

    # De-duplicate and filter by country
    unique_scraped = {}
    for job in scraped_jobs_list:
        if not is_job_in_target_country(job.get("location"), country):
            logger.info(f"Filtering out job outside target country ({country}): {job['title']} at {job['company']} (Location: {job['location']})")
            continue
            
        # Append URLs to description if not already present
        desc = job.get("description") or ""
        job_url = job.get("job_url")
        company_portal_url = job.get("company_portal_url")
        url_notes = []
        if job_url and f"Source Job Link: {job_url}" not in desc:
            url_notes.append(f"Source Job Link: {job_url}")
        if company_portal_url and f"Company Career Portal: {company_portal_url}" not in desc:
            url_notes.append(f"Company Career Portal: {company_portal_url}")
        if url_notes:
            job["description"] = desc + "\n\n---\n" + "\n".join(url_notes)
            
        unique_scraped[job["job_url"]] = job
        
    raw_jobs = list(unique_scraped.values())
    
    if raw_jobs:
        try:
            from actions_scraper.database import save_raw_jobs
            total_new = save_raw_jobs(raw_jobs)
            logger.info(f"Targeted scrape complete. Found {total_found} total, saved {total_new} raw staging jobs.")
            log_scrape_run(jobs_found=total_found, new_jobs=total_new, status="success")
        except Exception as e:
            logger.error(f"Error saving raw jobs to staging database: {str(e)}")
            log_scrape_run(jobs_found=total_found, new_jobs=0, status="failed", error_message=str(e))
    else:
        logger.info("Targeted scrape complete. No jobs to save.")
        log_scrape_run(jobs_found=total_found, new_jobs=0, status="success")
        
    return raw_jobs

if __name__ == "__main__":
    run_scraper_cycle()

def process_raw_jobs_batch(profile_settings=None):
    """
    Scans unprocessed raw jobs from DYNAMODB_JOBS_RAW_TABLE,
    performs AI classification (honoring Gemini rate limits),
    and saves them to the cleaned and production tables.
    """
    logger.info("Starting background raw jobs batch processing...")
    from actions_scraper.database import get_unprocessed_raw_jobs, save_cleaned_job, get_all_settings, get_target_companies
    
    settings = profile_settings or get_all_settings()
    target_companies = get_target_companies()
    
    unprocessed_jobs = get_unprocessed_raw_jobs()
    if not unprocessed_jobs:
        logger.info("No unprocessed raw jobs found. Processing finished.")
        return 0
        
    logger.info(f"Found {len(unprocessed_jobs)} unprocessed raw jobs to classify.")
    
    processed_count = 0
    
    target_names = {tc.get("name", "").lower().strip() for tc in target_companies}
    
    # Classify each unique job
    def classify_and_save_single_job(job):
        nonlocal processed_count
        try:
            logger.info(f"Processing/Classifying job: {job.get('title')} at {job.get('company')}")
            classified_job = process_job_classification(job, settings, target_companies)
            if save_cleaned_job(classified_job):
                processed_count += 1
                
                # Smart Company Harvesting
                company_name = job.get("company")
                if company_name:
                    cleaned_name = company_name.strip()
                    if cleaned_name.lower() not in target_names:
                        portal_url = None
                        job_url = job.get("job_url") or ""
                        company_portal_url = job.get("company_portal_url")
                        
                        if company_portal_url:
                            portal_url = company_portal_url
                        elif job_url:
                            url_lower = job_url.lower()
                            # Avoid adding general job boards
                            if not any(board in url_lower for board in ["linkedin.com", "indeed.com", "ziprecruiter.com", "glassdoor.com", "google.com", "jobspy"]):
                                portal_url = job_url
                                
                        if portal_url:
                            logger.info(f"Smart Harvesting: adding new company {cleaned_name} with portal {portal_url}")
                            from actions_scraper.database import add_target_company
                            add_target_company(cleaned_name, portal_url)
                            target_names.add(cleaned_name.lower())
        except Exception as e:
            logger.error(f"Failed to process raw job {job.get('id', 'Unknown')}: {str(e)}")
            
    # Classifications are serialised internally in call_gemini_api by gemini_lock
    max_workers = min(len(unprocessed_jobs), 10)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(classify_and_save_single_job, job): job for job in unprocessed_jobs}
        for future in as_completed(futures):
            future.result()
            
    logger.info(f"Batch processing complete. Successfully classified and saved {processed_count} jobs.")
    return processed_count

def lambda_handler(event, context):
    search_term = event.get("search_term")
    location = event.get("location", "")
    if search_term:
        logger.info(f"[LAMBDA SCRAPER] Triggering targeted scrape via event: '{search_term}' in '{location}'")
        raw_jobs = run_targeted_scrape(search_term, location)
        # Classify the newly scraped raw jobs
        processed = process_raw_jobs_batch()
        return {
            "statusCode": 200,
            "body": f"Targeted scrape complete. Saved {len(raw_jobs)} raw jobs, processed {processed}."
        }
    else:
        logger.info("[LAMBDA SCRAPER] Triggering full scrape cycle")
        total_found, total_new = run_scraper_cycle()
        return {
            "statusCode": 200,
            "body": f"Scrape cycle complete. Found {total_found} jobs, saved/processed {total_new}."
        }

