import re
import requests
import logging
from datetime import datetime
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from backend.database import generate_job_id

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ats_scraper")

def slugify(text):
    """Convert company name to standard slug format."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text

def extract_slug_from_url(url, fallback_name):
    """
    Extracts the ATS board token/slug and the platform name from a company portal URL.
    Returns (slug, platform) e.g. ("stripe", "greenhouse"), ("figma", "lever"), ("stripe", "ashby"), or ("stripe/careers", "workday")
    """
    if not url:
        return slugify(fallback_name), "unknown"
        
    url_lower = url.lower().strip()
    
    # 1. Greenhouse URL parsing
    if "boards.greenhouse.io" in url_lower:
        # Check query param token first (e.g. ?board_token=stripe)
        match_token = re.search(r"board_token=([^&]+)", url)
        if match_token:
            return match_token.group(1), "greenhouse"
            
        # Check path pattern (e.g. boards.greenhouse.io/stripe)
        path_match = re.search(r"boards\.greenhouse\.io/([^/?#\s]+)", url)
        if path_match:
            slug = path_match.group(1)
            # greenhouse embed pages sometimes have embed/job_board
            if slug in ["embed", "embed-board"]:
                 match_embed = re.search(r"/embed/([^/?#\s]+)", url_lower)
                 if match_embed:
                     return match_embed.group(1), "greenhouse"
            return slug, "greenhouse"
            
    # 2. Lever URL parsing (e.g. jobs.lever.co/figma)
    if "jobs.lever.co" in url_lower:
        path_match = re.search(r"jobs\.lever\.co/([^/?#\s]+)", url)
        if path_match:
            return path_match.group(1), "lever"

    # 3. Ashby URL parsing (e.g. jobs.ashbyhq.com/figma)
    if "jobs.ashbyhq.com" in url_lower:
        path_match = re.search(r"jobs\.ashbyhq\.com/([^/?#\s]+)", url)
        if path_match:
            return path_match.group(1), "ashby"

    # 4. Workday URL parsing (e.g. company.myworkdayjobs.com/site)
    if "myworkdayjobs.com" in url_lower:
        host_match = re.search(r"https?://([^.]+)\.myworkdayjobs\.com", url_lower)
        if host_match:
            tenant = host_match.group(1)
            # Extract site name
            path_part = url.split("myworkdayjobs.com")[-1].strip("/")
            site = path_part.split("/")[0] if path_part else "careers"
            return f"{tenant}/{site}", "workday"
            
    # Fallback to slugifying the company name
    return slugify(fallback_name), "unknown"

def clean_html(html_content):
    """Strip HTML tags and format text description cleanly."""
    if not html_content:
        return ""
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        for el in soup.find_all(["p", "div", "br", "li", "h1", "h2", "h3", "h4", "h5"]):
            el.insert_after("\n")
        return soup.get_text().strip()
    except Exception as e:
        logger.error(f"Failed to parse description HTML: {str(e)}")
        return html_content

def scrape_greenhouse_portal(company_name, slug, search_terms, portal_url=None):
    """Scrapes jobs directly from Greenhouse corporate board API using slug."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
    logger.info(f"Checking Greenhouse portal for {company_name} using slug '{slug}' ({url})")
    
    jobs_found = []
    try:
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            data = response.json()
            postings = data.get("jobs", [])
            logger.info(f"Greenhouse found {len(postings)} total listings for {company_name}")
            
            terms_list = [t.strip().lower() for t in search_terms.split(",") if t.strip()]
            
            for post in postings:
                title = post.get("title", "")
                title_lower = title.lower()
                
                matches_term = any(term in title_lower for term in terms_list) if terms_list else True
                if not matches_term:
                    continue
                    
                location = post.get("location", {}).get("name", "Unknown")
                job_url = post.get("absolute_url", "")
                html_desc = post.get("content", "")
                description = clean_html(html_desc)
                
                jobs_found.append({
                    "id": generate_job_id(company_name, title, location),
                    "job_url": job_url,
                    "title": title,
                    "company": company_name,
                    "location": location,
                    "source": "company_portal (greenhouse)",
                    "posted_date": datetime.today().strftime('%Y-%m-%d'),
                    "salary": "Not disclosed",
                    "description": description,
                    "company_portal_url": portal_url or f"https://boards.greenhouse.io/{slug}"
                })
        else:
            logger.info(f"Greenhouse portal not active for slug '{slug}' (HTTP {response.status_code})")
            if response.status_code == 403:
                from backend.database import log_portal_error
                log_portal_error(company_name, portal_url or f"https://boards.greenhouse.io/{slug}", 403, "Forbidden")
    except Exception as e:
        logger.error(f"Error checking Greenhouse for slug '{slug}': {str(e)}")
        
    return jobs_found

def scrape_lever_portal(company_name, slug, search_terms, portal_url=None):
    """Scrapes jobs directly from Lever corporate board API using slug."""
    url = f"https://api.lever.co/v0/postings/{slug}"
    logger.info(f"Checking Lever portal for {company_name} using slug '{slug}' ({url})")
    
    jobs_found = []
    try:
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            postings = response.json()
            logger.info(f"Lever found {len(postings)} total listings for {company_name}")
            
            terms_list = [t.strip().lower() for t in search_terms.split(",") if t.strip()]
            
            for post in postings:
                title = post.get("title", "")
                title_lower = title.lower()
                
                matches_term = any(term in title_lower for term in terms_list) if terms_list else True
                if not matches_term:
                    continue
                    
                location = post.get("categories", {}).get("location", "Unknown")
                job_url = post.get("hostedUrl", "")
                
                desc_html_parts = []
                if post.get("descriptionHtml"):
                    desc_html_parts.append(post.get("descriptionHtml"))
                for section in post.get("lists", []):
                    desc_html_parts.append(f"<h3>{section.get('text', '')}</h3>")
                    desc_html_parts.append(section.get("content", ""))
                if post.get("additionalHtml"):
                    desc_html_parts.append(post.get("additionalHtml"))
                    
                full_html = "\n".join(desc_html_parts)
                description = clean_html(full_html)
                
                jobs_found.append({
                    "id": generate_job_id(company_name, title, location),
                    "job_url": job_url,
                    "title": title,
                    "company": company_name,
                    "location": location,
                    "source": "company_portal (lever)",
                    "posted_date": datetime.today().strftime('%Y-%m-%d'),
                    "salary": "Not disclosed",
                    "description": description,
                    "company_portal_url": portal_url or f"https://jobs.lever.co/{slug}"
                })
        else:
            logger.info(f"Lever portal not active for slug '{slug}' (HTTP {response.status_code})")
            if response.status_code == 403:
                from backend.database import log_portal_error
                log_portal_error(company_name, portal_url or f"https://jobs.lever.co/{slug}", 403, "Forbidden")
    except Exception as e:
        logger.error(f"Error checking Lever for slug '{slug}': {str(e)}")
        
    return jobs_found

def scrape_general_html_portal(company_name, portal_url, search_terms):
    """
    Heuristically scrapes general HTML corporate/state/government career portals.
    Finds job links matching search terms.
    """
    import random
    import time
    from urllib.parse import urljoin
    
    # Human-like sleep to avoid rate limits / blocking
    time.sleep(random.uniform(0.5, 2.0))
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.google.com/"
    }
    
    logger.info(f"Scraping general HTML portal for {company_name} at {portal_url}")
    jobs_found = []
    
    try:
        response = requests.get(portal_url, headers=headers, timeout=10)
        if response.status_code != 200:
            logger.info(f"Failed to fetch general portal {portal_url} - HTTP {response.status_code}")
            if response.status_code == 403:
                from backend.database import log_portal_error
                log_portal_error(company_name, portal_url, 403, "Forbidden")
            return []
            
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Look for all anchor links
        links = soup.find_all("a", href=True)
        terms_list = [t.strip().lower() for t in search_terms.split(",") if t.strip()]
        
        seen_urls = set()
        
        for link in links:
            href = link["href"].strip()
            # Resolve relative URLs
            full_url = urljoin(portal_url, href)
            
            # Avoid duplicate job links
            if full_url in seen_urls:
                continue
                
            text = link.get_text(strip=True)
            text_lower = text.lower()
            href_lower = href.lower()
            
            # Basic validation: must be a http/https link
            if not (full_url.startswith("http://") or full_url.startswith("https://")):
                continue
                
            # Filter out social links, terms, privacy, etc.
            if any(x in href_lower for x in ["facebook.com", "twitter.com", "linkedin.com", "instagram.com", "youtube.com", "privacy", "terms", "about-us", "contact"]):
                continue
                
            # Heuristic to check if this looks like a job link.
            # Usually job links either have "job", "career", "vacancy", "posting", "opening", "detail", "apply" in URL,
            # or the link text itself matches our job search terms.
            is_job_href = any(k in href_lower for k in ["/job", "/careers", "/vacancy", "/opening", "posting", "detail", "apply", "/position", "job-id", "jobid", "showjob"])
            matches_term = any(term in text_lower for term in terms_list) if terms_list else True
            
            # If the href matches job patterns AND text matches search terms (or search terms matches href)
            if matches_term and (is_job_href or any(term in href_lower for term in terms_list)):
                # Clean up title
                title = text if len(text) > 5 else href.split("/")[-1].replace("-", " ").replace("_", " ").title()
                # If title is still too short or looks like "Apply", look at parent text or use clean fallback
                if len(title) < 5 or title.lower() in ["apply", "apply now", "view job", "details", "learn more", "read more"]:
                    parent_text = link.parent.get_text(" ", strip=True) if link.parent else ""
                    if parent_text and len(parent_text) > 10:
                        title = parent_text[:100] + "..." if len(parent_text) > 100 else parent_text
                    else:
                        title = f"{company_name} Job Posting"
                
                # Heuristically check for location in link text or parent text
                location = "Unknown"
                parent_text = link.parent.get_text(" ", strip=True) if link.parent else ""
                loc_matches = re.findall(r'\b(remote|hybrid|on-site|onsite|new york|nyc|san francisco|sf|chicago|london|remote usa|united states)\b', parent_text.lower())
                if loc_matches:
                    location = loc_matches[0].title()
                
                job_id = generate_job_id(company_name, title, location)
                
                # Snippet of surrounding context as description
                description = parent_text if len(parent_text) > len(text) else f"Job opportunity for {title} at {company_name}."
                if len(description) > 500:
                    description = description[:500] + "..."
                
                jobs_found.append({
                    "id": job_id,
                    "job_url": full_url,
                    "title": title,
                    "company": company_name,
                    "location": location,
                    "source": "company_portal (custom)",
                    "posted_date": datetime.today().strftime('%Y-%m-%d'),
                    "salary": "Not disclosed",
                    "description": description,
                    "company_portal_url": portal_url
                })
                seen_urls.add(full_url)
                
                # Limit number of parsed jobs per general page to 10 to avoid spamming/clutter
                if len(jobs_found) >= 10:
                    break
                    
    except Exception as e:
        logger.error(f"Error scraping general HTML portal for {company_name}: {str(e)}")
        
    return jobs_found

def scrape_ashby_portal(company_name, slug, search_terms, portal_url=None):
    """Scrapes jobs directly from Ashby public board API using slug."""
    url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true"
    logger.info(f"Checking Ashby portal for {company_name} using slug '{slug}' ({url})")
    
    jobs_found = []
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            postings = data.get("jobs", [])
            logger.info(f"Ashby found {len(postings)} total listings for {company_name}")
            
            terms_list = [t.strip().lower() for t in search_terms.split(",") if t.strip()]
            
            for post in postings:
                title = post.get("title", "")
                title_lower = title.lower()
                
                matches_term = any(term in title_lower for term in terms_list) if terms_list else True
                if not matches_term:
                    continue
                    
                location = post.get("location", "Unknown")
                job_url = post.get("jobUrl") or f"https://jobs.ashbyhq.com/{slug}/{post.get('id')}"
                
                comp = post.get("compensation", {})
                salary = "Not disclosed"
                if comp:
                    cur = comp.get("currencyCode", "")
                    min_val = comp.get("minValue")
                    max_val = comp.get("maxValue")
                    if min_val and max_val:
                        salary = f"{cur} {min_val} - {max_val}"
                    elif min_val:
                        salary = f"{cur} {min_val}+"
                        
                description = clean_html(post.get("descriptionHtml") or post.get("description", ""))
                
                jobs_found.append({
                    "id": generate_job_id(company_name, title, location),
                    "job_url": job_url,
                    "title": title,
                    "company": company_name,
                    "location": location,
                    "source": "company_portal (ashby)",
                    "posted_date": datetime.today().strftime('%Y-%m-%d'),
                    "salary": salary,
                    "description": description,
                    "company_portal_url": portal_url or f"https://jobs.ashbyhq.com/{slug}"
                })
        else:
            logger.info(f"Ashby portal not active for slug '{slug}' (HTTP {response.status_code})")
            if response.status_code == 403:
                from backend.database import log_portal_error
                log_portal_error(company_name, portal_url or f"https://jobs.ashbyhq.com/{slug}", 403, "Forbidden")
    except Exception as e:
        logger.error(f"Error checking Ashby for slug '{slug}': {str(e)}")
        
    return jobs_found

def scrape_workday_portal(company_name, slug, search_terms, portal_url=None):
    """Scrapes jobs directly from Workday CXS API using tenant/site slug."""
    if "/" in slug:
        tenant, site = slug.split("/", 1)
    else:
        tenant = slug
        site = "careers"
        
    url = f"https://{tenant}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"
    logger.info(f"Checking Workday portal for {company_name} using tenant '{tenant}' and site '{site}' ({url})")
    
    jobs_found = []
    try:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        payload = {
            "appliedFacets": {},
            "limit": 50,
            "offset": 0,
            "searchText": ""
        }
        response = requests.post(url, json=payload, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            postings = data.get("jobPostings", [])
            logger.info(f"Workday found {len(postings)} total listings for {company_name}")
            
            terms_list = [t.strip().lower() for t in search_terms.split(",") if t.strip()]
            
            for post in postings:
                title = post.get("title", "")
                title_lower = title.lower()
                
                matches_term = any(term in title_lower for term in terms_list) if terms_list else True
                if not matches_term:
                    continue
                    
                location = post.get("locationsText") or "Unknown"
                external_path = post.get("externalPath", "")
                job_url = f"https://{tenant}.myworkdayjobs.com{external_path}"
                
                description = f"Job opportunity for {title} at {company_name}. Please apply directly via {job_url}."
                
                jobs_found.append({
                    "id": generate_job_id(company_name, title, location),
                    "job_url": job_url,
                    "title": title,
                    "company": company_name,
                    "location": location,
                    "source": "company_portal (workday)",
                    "posted_date": datetime.today().strftime('%Y-%m-%d'),
                    "salary": "Not disclosed",
                    "description": description,
                    "company_portal_url": portal_url or f"https://{tenant}.myworkdayjobs.com/{site}"
                })
        else:
            logger.info(f"Workday portal not active for slug '{slug}' (HTTP {response.status_code})")
            if response.status_code == 403:
                from backend.database import log_portal_error
                log_portal_error(company_name, portal_url or f"https://{tenant}.myworkdayjobs.com/{site}", 403, "Forbidden")
    except Exception as e:
        logger.error(f"Error checking Workday for slug '{slug}': {str(e)}")
        
    return jobs_found

def scrape_single_company(company_info, search_terms):
    if isinstance(company_info, dict):
        name = company_info.get("name")
        url = company_info.get("portal_url")
    else:
        name = company_info
        url = None
        
    slug, platform = extract_slug_from_url(url, name)
    
    if platform == "greenhouse":
        return scrape_greenhouse_portal(name, slug, search_terms, url)
    elif platform == "lever":
        return scrape_lever_portal(name, slug, search_terms, url)
    elif platform == "ashby":
        return scrape_ashby_portal(name, slug, search_terms, url)
    elif platform == "workday":
        return scrape_workday_portal(name, slug, search_terms, url)
    else:
        if url:
            return scrape_general_html_portal(name, url, search_terms)
        return []

def scrape_all_company_portals(target_companies, search_terms):
    """Runs Greenhouse and Lever scans for all target companies in parallel using a ThreadPoolExecutor."""
    portal_jobs = []
    
    # We use a ThreadPoolExecutor with 50 concurrent workers to avoid overloading but keep it fast
    max_workers = min(len(target_companies), 50)
    
    logger.info(f"Starting parallel corporate portal scrape for {len(target_companies)} companies using {max_workers} workers...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_company = {
            executor.submit(scrape_single_company, company, search_terms): company 
            for company in target_companies
        }
        
        # Gather results as they complete
        for future in as_completed(future_to_company):
            try:
                jobs = future.result()
                if jobs:
                    portal_jobs.extend(jobs)
            except Exception as e:
                company = future_to_company[future]
                logger.error(f"Error scraping company {company}: {str(e)}")
                
    logger.info(f"Finished parallel corporate portal scrape. Retrieved {len(portal_jobs)} matching postings.")
    return portal_jobs
