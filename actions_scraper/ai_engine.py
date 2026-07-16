import re
import json
import requests
import logging
import time
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ai_engine")

gemini_lock = threading.Lock()
last_gemini_call_time = 0.0



def clean_salary(salary_text, description_text):
    """Try to extract salary range from text if not provided in metadata."""
    if salary_text and len(salary_text.strip()) > 2:
        return salary_text.strip()

    # Regex search in description for formats like $120,000 - $150,000 or $120k-$150k
    salary_patterns = [
        r"\$[0-9]{2,3},?[0-9]{0,3}\s*-\s*\$[0-9]{2,3},?[0-9]{0,3}\s*(?:a year|per year|annually|/yr)?",
        r"\$[0-9]{2,3}\s*[kK]\s*-\s*\$[0-9]{2,3}\s*[kK]",
        r"\$[0-9]{2,3}\s*-\s*\$[0-9]{2,3}\s*(?:an hour|per hour|/hr)?"
    ]

    if description_text:
        for pattern in salary_patterns:
            match = re.search(pattern, description_text)
            if match:
                return match.group(0)
    return "Not disclosed"


def parse_state(location):
    """Extract standard US 2-letter state code from location string."""
    if not location:
        return "Remote"
    # Match standard state abbreviations like Dallas, TX or Remote, DE
    match = re.search(r"\\b([A-Z]{2})\\b", location)
    if match:
        return match.group(1)
    if "remote" in location.lower():
        return "Remote"
    return "Unknown"


def build_structured_data_heuristics(title, description):
    """Advanced regex heuristic description organizer.
    Breaks down a raw text job description into clean structured sections."""
    desc_lower = description.lower() if description else ""

    # 1. Tech Stack keywords search
    common_tech = [
        "python", "javascript", "typescript", "react", "vue", "angular", "node",
        "fastapi", "django", "flask", "ruby", "rails", "golang", "rust", "java",
        "c++", "c#", "dotnet", "aws", "azure", "gcp", "docker", "kubernetes",
        "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
        "spark", "hadoop", "snowflake", "dbt", "machine learning", "tensorflow",
        "pytorch", "llm", "ai", "html", "css", "graphql", "rest api", "terraform"
    ]
    tech_found = []
    for tech in common_tech:
        pattern = r"\b" + re.escape(tech) + r"\b"
        if re.search(pattern, desc_lower):
            tech_map = {"c++": "C++", "c#": "C#", "dotnet": ".NET", "aws": "AWS", "gcp": "GCP", "sql": "SQL", "dbt": "dbt", "llm": "LLMs", "html": "HTML", "css": "CSS", "rest api": "REST APIs", "terraform": "Terraform"}
            tech_found.append(tech_map.get(tech, tech.title()))

    # 2. Role Overview: extract first 2 sentences
    sentences = re.split(r'(?<=\.|!|\?)\s+', description) if description else []
    overview = " ".join(sentences[:2]) if sentences else "No description summary available."
    if len(overview) > 300:
        overview = overview[:297] + "..."

    # 3. Categorized list extraction
    responsibilities = []
    qualifications = []
    benefits = []
    lines = [line.strip() for line in description.split("\n") if line.strip()] if description else []
    current_section = None
    for line in lines:
        line_lower = line.lower()
        if any(h in line_lower for h in ["responsibilities", "what you'll do", "what you will do", "the role", "job duties", "key tasks"]):
            current_section = "responsibilities"
            continue
        elif any(h in line_lower for h in ["requirements", "qualifications", "what you bring", "what you need", "skills", "experience required"]):
            current_section = "qualifications"
            continue
        elif any(h in line_lower for h in ["benefits", "what we offer", "perks", "compensation", "why join"]):
            current_section = "benefits"
            continue
        
        is_bullet = re.match(r"^[-*•+]?\s*|^\d+\.\s*", line)
        if is_bullet:
            cleaned_line = re.sub(r"^[-*•+]?\s*|^\d+\.\s*", "", line).strip()
            if not cleaned_line or len(cleaned_line) < 10:
                continue
            if current_section == "responsibilities" and len(responsibilities) < 6:
                responsibilities.append(cleaned_line)
            elif current_section == "qualifications" and len(qualifications) < 6:
                qualifications.append(cleaned_line)
            elif current_section == "benefits" and len(benefits) < 6:
                benefits.append(cleaned_line)

    # Fallbacks
    if not responsibilities:
        for line in lines:
            if re.match(r"^[-*•+]?\s*|^\d+\.\s*", line) and len(responsibilities) < 5:
                cleaned = re.sub(r"^[-*•+]?\s*|^\d+\.\s*", "", line).strip()
                if len(cleaned) > 15:
                    responsibilities.append(cleaned)
    if not qualifications:
        for line in lines:
            if any(k in line.lower() for k in ["degree", "experience", "years of", "required", "bachelor", "skills"]):
                cleaned = re.sub(r"^[-*•+]?\s*|^\d+\.\s*", "", line).strip()
                if cleaned not in responsibilities and len(cleaned) > 15 and len(qualifications) < 5:
                    qualifications.append(cleaned)
    if not benefits:
        for line in lines:
            if any(k in line.lower() for k in ["401k", "401(k)", "insurance", "dental", "vision", "pto", "benefits", "vacation", "health"]):
                cleaned = re.sub(r"^[-*•+]?\s*|^\d+\.\s*", "", line).strip()
                if cleaned not in responsibilities and cleaned not in qualifications and len(cleaned) > 10 and len(benefits) < 4:
                    benefits.append(cleaned)

    # Absolute fallback defaults if lists are still empty
    if not responsibilities:
        responsibilities = ["Execute software development tasks.", "Collaborate with cross-functional engineering teams.", "Maintain high-quality clean codebase."]
    if not qualifications:
        qualifications = ["Relevant software development experience.", "Strong analytical and problem-solving skills.", "Experience with target technical stack."]
    if not benefits:
        benefits = ["Standard company benefits packages apply."]

    return {
        "role_overview": overview,
        "tech_stack": tech_found[:12],
        "responsibilities": responsibilities,
        "qualifications": qualifications,
        "benefits": benefits
    }


def classify_heuristics(title, company, location, description, target_companies, search_terms, resume_text):
    """Rule-based heuristic classifier to precisely scope job details offline."""
    title_lower = (title or "").lower()
    company_lower = (company or "").lower()
    loc_lower = (location or "").lower()
    desc_lower = (description or "").lower()
    res_lower = (resume_text or "").lower()

    # 1. Remote Type
    remote_type = "onsite"
    if any(k in loc_lower for k in ["remote", "wfh", "work from home", "anywhere", "telecommute"]):
        remote_type = "remote"
    elif any(k in loc_lower or k in desc_lower for k in ["hybrid", "flexible location", "partial remote", "in-office 2 days", "in-office 3 days"]):
        remote_type = "hybrid"
    elif any(k in desc_lower for k in ["work from home", "wfh", "100% remote", "fully remote"]):
        remote_type = "remote"

    # 2. Visa Type
    visa_type = "unknown"
    sponsorship_negatives = [
        "no sponsorship", "does not sponsor", "cannot sponsor", "not sponsor", "unable to sponsor", 
        "no h1b", "must be us citizen", "green card required", "us citizen only", "no visa sponsorship"
    ]
    sponsorship_positives = [
        "h1b sponsorship", "visa sponsorship", "will sponsor", "h-1b transfer", "opt/cpt", 
        "sponsorship is available", "sponsorship available", "open to sponsor"
    ]
    has_neg = any(neg in desc_lower for neg in sponsorship_negatives)
    has_pos = any(pos in desc_lower for pos in sponsorship_positives) or "h1b" in desc_lower or "h-1b" in desc_lower
    if has_neg:
        visa_type = "none"
    elif has_pos:
        visa_type = "h1b"

    # 3. Contract Type
    contract_type = "full-time"
    if any(k in title_lower or k in desc_lower for k in ["intern", "co-op", "coop", "fellow", "internship"]):
        contract_type = "internship"
    elif "c2c" in desc_lower or "corp-to-corp" in desc_lower or "corp to corp" in desc_lower:
        contract_type = "c2c"
    elif "1099" in desc_lower:
        contract_type = "contract"
    elif "w2" in desc_lower or "w-2" in desc_lower:
        if "contract" in desc_lower or "contractor" in desc_lower:
            contract_type = "contract"
        else:
            contract_type = "w2"
    elif any(k in desc_lower or k in title_lower for k in ["contract", "contractor", "temporary"]):
        contract_type = "contract"
    elif "part-time" in desc_lower or "part time" in desc_lower:
        contract_type = "part-time"

    # 4. Relevance Scoring (Sophisticated offline matching)
    score = 40  # Base score
    reason_items = []

    # Title match score (higher weight)
    terms_list = [term.strip().lower() for term in (search_terms or "").split(",") if term.strip()]
    matched_term = None
    for term in terms_list:
        if re.search(r"\b" + re.escape(term) + r"\b", title_lower):
            score += 35
            matched_term = term
            reason_items.append(f"Title matches search term '{term}' precisely.")
            break
    if not matched_term:
        # Partial match check
        for term in terms_list:
            words = term.split()
            if len(words) > 1 and all(w in title_lower for w in words):
                score += 20
                matched_term = term
                reason_items.append(f"Title partially matches search term '{term}'.")
                break

    # Target company score
    is_target_company = False
    for tc in target_companies:
        tc_name = tc.get("name", "") if isinstance(tc, dict) else tc
        if tc_name.lower() in company_lower:
            is_target_company = True
            score += 25
            reason_items.append(f"Posted by target focus company '{tc_name}'.")
            break

    # Skills overlap score
    skills = [
        "python", "javascript", "typescript", "react", "vue", "angular", "node",
        "fastapi", "django", "flask", "ruby", "rails", "golang", "rust", "java",
        "c++", "c#", "aws", "azure", "gcp", "docker", "kubernetes", "sql", "postgres",
        "spark", "hadoop", "snowflake", "dbt", "tensorflow", "pytorch", "llm", "ai", "terraform"
    ]
    matched_skills = []
    if res_lower:
        for skill in skills:
            pattern = r"\b" + re.escape(skill) + r"\b"
            if re.search(pattern, desc_lower) and re.search(pattern, res_lower):
                matched_skills.append(skill)
        
        if matched_skills:
            skills_score = min(len(matched_skills) * 4, 20)
            score += skills_score
            reason_items.append(f"Matches your resume skills: {', '.join(matched_skills[:5])}.")

    # Remote preference score
    if remote_type == "remote":
        score += 10
        reason_items.append("Position is Remote.")
    elif remote_type == "hybrid":
        score += 5
        reason_items.append("Position is Hybrid.")

    # Bound the score
    score = max(0, min(score, 100))

    # Red Flags check
    red_flag_terms = ["rockstar", "ninja", "guru", "family", "work hard play hard", "fast-paced", "tight deadlines", "under pressure"]
    found_flags = []
    for flag in red_flag_terms:
        if re.search(r"\b" + re.escape(flag) + r"\b", desc_lower):
            found_flags.append(flag.title())
            
    reason = " | ".join(reason_items) if reason_items else "Matched baseline parameters."

    # Personalized Outreach Pitch
    skills_text = f" in {', '.join(matched_skills[:3])}" if matched_skills else ""
    outreach_pitch = (
        f"Hi Hiring Team,\n\n"
        f"I recently saw the opening for the {title} position at {company} and wanted to express my interest. "
        f"With my background in software engineering{skills_text}, I believe I could contribute effectively to your engineering goals.\n\n"
        f"I would welcome the opportunity to discuss the role and see how my experience aligns with your current priorities. "
        f"Thank you for your time and consideration.\n\n"
        f"Best regards,\n[Your Name]"
    )

    return {
        "remote_type": remote_type,
        "visa_type": visa_type,
        "contract_type": contract_type,
        "score": score,
        "reason": reason,
        "red_flags": json.dumps(found_flags),
        "outreach_pitch": outreach_pitch
    }

def call_api_with_retry(request_fn, provider_name, max_retries=5, initial_backoff=2):
    backoff = initial_backoff
    for attempt in range(max_retries):
        try:
            response = request_fn()
            if response.status_code == 200:
                return response, None
            elif response.status_code == 429:
                try:
                    err_text = response.text
                    if "quota" in err_text.lower() or "billing" in err_text.lower():
                        return None, f"{provider_name} API quota exceeded or billing issue. Please check your AI console settings."
                except Exception:
                    pass
                sleep_time = backoff ** attempt
                logger.warning(f"{provider_name} API 429 rate limit hit. Retrying in {sleep_time}s (attempt {attempt + 1}/{max_retries})...")
                time.sleep(sleep_time)
            else:
                # If it's a transient server error (500, 502, 503, 504), we should also retry
                if response.status_code in [500, 502, 503, 504]:
                    sleep_time = backoff ** attempt
                    logger.warning(f"{provider_name} API transient error {response.status_code} hit. Retrying in {sleep_time}s (attempt {attempt + 1}/{max_retries})...")
                    time.sleep(sleep_time)
                else:
                    return None, f"{provider_name} API returned status {response.status_code}"
        except Exception as e:
            if attempt == max_retries - 1:
                return None, f"Failed to communicate with {provider_name} API: {str(e)}"
            time.sleep(backoff ** attempt)
    return None, f"{provider_name} API returned status 429 (rate limit exceeded after retries)"

def call_gemini_api(prompt, model, api_key, expect_json=True):
    global last_gemini_call_time
    with gemini_lock:
        now = time.time()
        elapsed = now - last_gemini_call_time
        min_interval = 4.2  # Ensures we don't exceed 15 requests per minute
        if elapsed < min_interval:
            sleep_time = min_interval - elapsed
            logger.info(f"Gemini API rate limiter: sleeping {sleep_time:.2f}s to maintain spacing")
            time.sleep(sleep_time)
        
        last_gemini_call_time = time.time()
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        if expect_json:
            payload["generationConfig"] = {
                "responseMimeType": "application/json"
            }
        
        def make_req():
            return requests.post(url, json=payload, headers=headers, timeout=60)
            
        response, err = call_api_with_retry(make_req, "Gemini")
        if err:
            return {"error": err}
            
        try:
            res_data = response.json()
            text = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
            if expect_json:
                if text.startswith("```"):
                    text = re.sub(r"^```json\s*|```$", "", text, flags=re.MULTILINE).strip()
                return json.loads(text)
            return text
        except Exception as e:
            logger.error(f"Failed to parse Gemini response: {e}. Raw: {response.text if 'response' in locals() and response else 'No response'}")
            return {"error": "Failed to parse Gemini response"}


def call_openai_api(prompt, model, api_key, expect_json=True):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    if expect_json:
        payload["response_format"] = {"type": "json_object"}
        
    def make_req():
        return requests.post(url, json=payload, headers=headers, timeout=60)
        
    response, err = call_api_with_retry(make_req, "OpenAI")
    if err:
        return {"error": err}
        
    try:
        res_data = response.json()
        text = res_data["choices"][0]["message"]["content"].strip()
        if expect_json:
            if text.startswith("```"):
                text = re.sub(r"^```json\s*|```$", "", text, flags=re.MULTILINE).strip()
            return json.loads(text)
        return text
    except Exception as e:
        logger.error(f"Failed to parse OpenAI response: {e}. Raw: {response.text}")
        return {"error": "Failed to parse OpenAI response"}

def call_claude_api(prompt, model, api_key, expect_json=True):
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    # Map retired model names to active equivalents
    model_mapped = model
    if model_mapped:
        model_mapped = model_mapped.strip().lower()
        mapping = {
            "claude-3-5-haiku-latest": "claude-haiku-4-5",
            "claude-3-5-haiku-20241022": "claude-haiku-4-5",
            "claude-3-5-sonnet-latest": "claude-sonnet-4-6",
            "claude-3-5-sonnet-20241022": "claude-sonnet-4-6",
            "claude-3-5-sonnet-20240620": "claude-sonnet-4-6",
            "claude-3-7-sonnet-latest": "claude-sonnet-4-6",
            "claude-3-7-sonnet-20250219": "claude-sonnet-4-6"
        }
        if model_mapped in mapping:
            logger.info(f"Mapping retired Claude model '{model}' to active replacement '{mapping[model_mapped]}'")
            model_mapped = mapping[model_mapped]
        else:
            model_mapped = model # Keep original casing/value if not in mapping
    else:
        model_mapped = "claude-sonnet-4-6"

    payload = {
        "model": model_mapped,
        "max_tokens": 4096,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    def make_req():
        return requests.post(url, json=payload, headers=headers, timeout=60)
        
    response, err = call_api_with_retry(make_req, "Claude")
    if err:
        return {"error": err}
        
    try:
        res_data = response.json()
        text = res_data["content"][0]["text"].strip()
        if expect_json:
            if text.startswith("```"):
                text = re.sub(r"^```json\s*|```$", "", text, flags=re.MULTILINE).strip()
            return json.loads(text)
        return text
    except Exception as e:
        logger.error(f"Failed to parse Claude response: {e}. Raw: {response.text}")
        return {"error": "Failed to parse Claude response"}

def call_groq_api(prompt, model, api_key, expect_json=True):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": model or "llama3-8b-8192",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    if expect_json:
        payload["response_format"] = {"type": "json_object"}
        
    def make_req():
        return requests.post(url, json=payload, headers=headers, timeout=60)
        
    response, err = call_api_with_retry(make_req, "Groq")
    if err:
        return {"error": err}
        
    try:
        res_data = response.json()
        text = res_data["choices"][0]["message"]["content"].strip()
        if expect_json:
            if text.startswith("```"):
                text = re.sub(r"^```json\s*|```$", "", text, flags=re.MULTILINE).strip()
            return json.loads(text)
        return text
    except Exception as e:
        logger.error(f"Failed to parse Groq response: {e}. Raw: {response.text}")
        return {"error": "Failed to parse Groq response"}

def call_grok_api(prompt, model, api_key, expect_json=True):
    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": model or "grok-beta",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    if expect_json:
        payload["response_format"] = {"type": "json_object"}
        
    def make_req():
        return requests.post(url, json=payload, headers=headers, timeout=60)
        
    response, err = call_api_with_retry(make_req, "Grok")
    if err:
        return {"error": err}
        
    try:
        res_data = response.json()
        text = res_data["choices"][0]["message"]["content"].strip()
        if expect_json:
            if text.startswith("```"):
                text = re.sub(r"^```json\s*|```$", "", text, flags=re.MULTILINE).strip()
            return json.loads(text)
        return text
    except Exception as e:
        logger.error(f"Failed to parse Grok response: {e}. Raw: {response.text}")
        return {"error": "Failed to parse Grok response"}

def call_deepseek_api(prompt, model, api_key, expect_json=True):
    url = "https://api.deepseek.com/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    m = model or "deepseek-v4-flash"
    payload = {
        "model": m,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    if expect_json:
        payload["response_format"] = {"type": "json_object"}
        
    def make_req():
        return requests.post(url, json=payload, headers=headers, timeout=60)
        
    response, err = call_api_with_retry(make_req, "DeepSeek")
    if err:
        return {"error": err}
        
    try:
        res_data = response.json()
        text = res_data["choices"][0]["message"]["content"].strip()
        if expect_json:
            if text.startswith("```"):
                text = re.sub(r"^```json\s*|```$", "", text, flags=re.MULTILINE).strip()
            return json.loads(text)
        return text
    except Exception as e:
        logger.error(f"Failed to parse DeepSeek response: {e}. Raw: {response.text}")
        return {"error": "Failed to parse DeepSeek response"}

def get_aligned_credentials(provider, model, api_key):
    """
    Parses comma-separated inputs for provider, model, and api_key.
    Aligns them by index, replicating/reusing the last items if lengths differ.
    """
    providers = [p.strip() for p in (provider or "").split(",") if p.strip()]
    models = [m.strip() for m in (model or "").split(",") if m.strip()]
    keys = [k.strip() for k in (api_key or "").split(",") if k.strip()]
    
    if not keys:
        return []
        
    pairs = []
    for i, key in enumerate(keys):
        # Align provider
        if providers:
            p = providers[i] if i < len(providers) else providers[-1]
        else:
            p = "gemini"
            
        # Align model
        if models:
            m = models[i] if i < len(models) else models[-1]
        else:
            m = ""
            
        pairs.append({
            "provider": p,
            "model": m,
            "api_key": key
        })
    return pairs

def call_single_ai_model(prompt, provider, model, api_key, expect_json=True):
    if not provider or not api_key:
        return {"error": "AI provider and API key must be specified."}
    
    prov = provider.lower().strip()
    if "gemini" in prov:
        m = model or "gemini-1.5-flash"
        return call_gemini_api(prompt, m, api_key, expect_json)
    elif "openai" in prov or "chatgpt" in prov or "chatgptx" in prov:
        m = model or "gpt-4o-mini"
        return call_openai_api(prompt, m, api_key, expect_json)
    elif "claude" in prov or "anthropic" in prov:
        m = model or "claude-sonnet-4-6"
        return call_claude_api(prompt, m, api_key, expect_json)
    elif "gorx" in prov or "grok" in prov or "xai" in prov:
        m = model or "grok-beta"
        return call_grok_api(prompt, m, api_key, expect_json)
    elif "groq" in prov:
        m = model or "llama3-8b-8192"
        return call_groq_api(prompt, m, api_key, expect_json)
    elif "deepseek" in prov:
        m = model or "deepseek-v4-flash"
        return call_deepseek_api(prompt, m, api_key, expect_json)
    else:
        return {"error": f"Unsupported AI provider: {provider}"}

def call_ai_model(prompt, provider, model, api_key, expect_json=True):
    if not provider or not api_key:
        return {"error": "AI provider and API key must be specified."}
        
    credentials = get_aligned_credentials(provider, model, api_key)
    if not credentials:
        return {"error": "No valid API keys specified in settings."}
        
    last_err = None
    all_errors = []
    for i, cred in enumerate(credentials):
        p = cred["provider"]
        m = cred["model"]
        k = cred["api_key"]
        
        logger.info(f"Attempting AI call with provider: {p}, model: {m} (key index {i+1}/{len(credentials)})")
        try:
            res = call_single_ai_model(prompt, p, m, k, expect_json)
            if isinstance(res, dict) and "error" in res:
                err_msg = res["error"]
                logger.warning(f"AI call failed with provider {p}, model {m} (key index {i+1}/{len(credentials)}): {err_msg}")
                all_errors.append(f"{p} ({m or 'default'}): {err_msg}")
                last_err = res
                # Fall over to next credential
                continue
            else:
                logger.info(f"AI call succeeded with provider {p}, model {m} (key index {i+1}/{len(credentials)})")
                return res
        except Exception as e:
            logger.exception(f"Unexpected exception with provider {p}, model {m} (key index {i+1}): {e}")
            all_errors.append(f"{p} ({m or 'default'}): Exception: {str(e)}")
            last_err = {"error": f"Exception: {str(e)}"}
            continue
            
    if all_errors:
        composite_err = " | ".join(all_errors)
        return {"error": f"All AI providers failed. Details: {composite_err}"}
    return last_err or {"error": "All configured AI providers and keys failed."}

def generate_cv_tailoring_with_ai(title, company, description, resume_text, provider, model, api_key):
    prompt = f"""
You are an expert mentor and senior executive recruiter with over 30 years of experience. Your goal is to help the candidate learn how to stand out and successfully get this job.
Analyze this job posting and the candidate's resume, and provide 3-5 high-impact, specific suggestions to tailor the resume (e.g. highlight key skills, rephrase bullets, frame achievements) for this role.

Job Title: {title}
Company: {company}
Job Description:\n{description}\n\nCandidate Resume:\n{resume_text if resume_text else 'Not provided. Treat candidate as a senior software developer.'}\n\nProvide your suggestions strictly as a JSON object with a single key \"tips\" which is a list of strings. Do not include markdown code blocks.
"""
    data = call_ai_model(prompt, provider, model, api_key, expect_json=True)
    if isinstance(data, dict) and data.get("error"):
        return {"status": "error", "tips": [], "error": data["error"]}
    if data and isinstance(data, dict):
        return {"status": "success", "tips": data.get("tips", [])}
    return {"status": "error", "tips": [], "error": "Failed to communicate with AI model."}

def generate_cover_letter_with_ai(title, company, description, resume_text, provider, model, api_key):
    prompt = f"""
You are an expert career coach and mentor with over 30 years of experience. Your goal is to write a highly compelling cover letter that highlights the candidate's strengths, aligns their experience with the job requirements, and helps them get a job.

Job Title: {title}
Company: {company}
Job Description:\n{description}\n\nCandidate Resume:\n{resume_text if resume_text else 'Not provided.'}\n\nReturn ONLY the letter text (no JSON, no markdown).
"""
    data = call_ai_model(prompt, provider, model, api_key, expect_json=False)
    if isinstance(data, dict) and data.get("error"):
        return {"status": "error", "cover_letter": "", "error": data["error"]}
    if isinstance(data, str):
        return {"status": "success", "cover_letter": data.strip()}
    return {"status": "error", "cover_letter": "", "error": "Failed to communicate with AI model."}

def generate_interview_prep_with_ai(title, company, description, resume_text, provider, model, api_key):
    prompt = f"""
You are a senior technical interviewer and mentor with over 30 years of experience. Your goal is to prepare the candidate to succeed in their upcoming interview, help them learn critical concepts, and get the job.
Generate 4-5 highly relevant interview questions (mix of technical and behavioral) for this specific role, along with detailed, high-impact answer/talking points for each based on their resume.

Job Title: {title}
Company: {company}
Job Description:\n{description}\n\nCandidate Resume:\n{resume_text if resume_text else 'Not provided. Assume candidate is a senior software engineer.'}\n\nProvide your output strictly as a JSON object with a single key "qa" containing a list of objects, each having "question" and "answer" keys. Do not include markdown code blocks.
"""
    data = call_ai_model(prompt, provider, model, api_key, expect_json=True)
    if isinstance(data, dict) and data.get("error"):
        return {"status": "error", "qa": [], "error": data["error"]}
    if data and isinstance(data, dict):
        return {"status": "success", "qa": data.get("qa", [])}
    return {"status": "error", "qa": [], "error": "Failed to communicate with AI model."}

def generate_outreach_templates_with_ai(title, company, description, resume_text, provider, model, api_key):
    prompt = f"""
You are a senior career consultant and networking mentor with over 30 years of experience. Your goal is to draft outreach templates that help the candidate build professional connections and get this job.

Job: {title} at {company}
Description:\n{description}\n\nCandidate Resume:\n{resume_text if resume_text else 'Not provided.'}\n\nPlease generate:
1. "linkedin_note": A connection request note under 300 characters.
2. "recruiter_email": A formal, personalized cold outreach email (120-180 words).
3. "followup_message": A concise follow-up email/message to send 1 week later.
\nProvide your output strictly as a JSON object with "linkedin_note", "recruiter_email", and "followup_message" keys. Do not include markdown code blocks.
"""
    data = call_ai_model(prompt, provider, model, api_key, expect_json=True)
    if isinstance(data, dict) and data.get("error"):
        return {"status": "error", "linkedin_note": "", "recruiter_email": "", "followup_message": "", "error": data["error"]}
    if data and isinstance(data, dict):
        return {
            "status": "success",
            "linkedin_note": data.get("linkedin_note", ""),
            "recruiter_email": data.get("recruiter_email", ""),
            "followup_message": data.get("followup_message", "")
        }
    return {"status": "error", "linkedin_note": "", "recruiter_email": "", "followup_message": "", "error": "Failed to communicate with AI model."}

def analyze_job_with_ai(title, company, location, salary, description, search_terms, target_companies, resume_text, provider, model, api_key):
    prompt = f"""
You are an expert talent acquisition consultant, senior recruiter, and career mentor with over 30 years of experience. Your goal is to evaluate if this job matches the candidate's profile and guide them on how to get it.

Candidate target titles/keywords: {search_terms}
Candidate Resume/Profile:\n{resume_text if resume_text else 'Not provided. Treat candidate as a standard Senior Software/Data Engineer.'}\n
Job Posting Details:
- Title: {title}
- Company: {company}
- Location: {location}
- Declared Salary: {salary}
- Description:\n{description}\n

Please evaluate this job posting. Provide your analysis strictly as a JSON object with the following fields:
1. "remote_type": one of ["remote", "hybrid", "onsite", "unknown"]
2. "visa_type": one of ["h1b", "none", "unknown"]
3. "contract_type": one of ["w2", "c2c", "contract", "full-time", "part-time", "internship", "unknown"]
4. "score": integer from 0 to 100 representing fit.
5. "reason": A bulleted summary (2-3 sentences) detailing why they fit or what they are missing.
6. "red_flags": A list of strings identifying recruiter red flags. Return empty list [] if none.
7. "outreach_pitch": A short, high-impact cold outreach message (100-150 words) customized to this job and the candidate's resume.
8. "structured_data": A nested JSON object organizing the job details:
   - "role_overview": A clean, high-level paragraph summarizing the position.
   - "tech_stack": A list of tools, programming languages, and technologies mentioned.
   - "responsibilities": A list of core responsibilities (3-6 key bullets).
   - "qualifications": A list of key required experience/certifications (3-6 key bullets).
   - "benefits": A list of benefits, perks, or compensation highlights.

Ensure the output is valid JSON and nothing else. Do not wrap in markdown code blocks.
"""
    data = call_ai_model(prompt, provider, model, api_key, expect_json=True)
    if data and isinstance(data, dict):
        if "red_flags" in data and isinstance(data["red_flags"], list):
            data["red_flags"] = json.dumps(data["red_flags"]).strip()
        elif "red_flags" not in data:
            data["red_flags"] = "[]"
        return data
    return None

def process_job_classification(job, db_settings, target_companies, provider=None, model=None, api_key=None):
    """Classifies job using local heuristics exclusively (no AI usage for background scraping)."""
    title = job.get("title", "")
    company = job.get("company", "")
    location = job.get("location", "")
    description = job.get("description", "")
    salary = clean_salary(job.get("salary", ""), description)

    search_terms = db_settings.get("search_terms", "")
    resume_text = db_settings.get("resume_text", "")

    # Always use local heuristics to save API quota and speed up scraping
    logger.info("Classifying job using local heuristics engine.")
    ai_data = classify_heuristics(
        title=title,
        company=company,
        location=location,
        description=description,
        target_companies=target_companies,
        search_terms=search_terms,
        resume_text=resume_text,
    )

    # Populate job dict
    job["salary"] = salary
    job["remote_type"] = ai_data.get("remote_type", "unknown")
    job["visa_type"] = ai_data.get("visa_type", "unknown")
    job["contract_type"] = ai_data.get("contract_type", "unknown")
    job["score"] = int(ai_data.get("score", 50))
    job["reason"] = ai_data.get("reason", "")
    job["red_flags"] = ai_data.get("red_flags", "[]")
    job["outreach_pitch"] = ai_data.get("outreach_pitch", "")
    job["company_portal_url"] = job.get("company_portal_url", None)

    # Structured data handling – ensure JSON string
    if "structured_data" in ai_data:
        job["structured_data"] = json.dumps(ai_data["structured_data"]) if not isinstance(ai_data["structured_data"], str) else ai_data["structured_data"]
    else:
        heur_struct = build_structured_data_heuristics(title, description)
        job["structured_data"] = json.dumps(heur_struct)

    return job


def generate_market_insights_with_ai(job_stats, provider, model, api_key):
    prompt = f"""
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
"""
    data = call_ai_model(prompt, provider, model, api_key, expect_json=True)
    if data and isinstance(data, dict):
        return data
    return {
        "booming_roles": ["AI/ML Engineer", "Cloud Architect", "Cybersecurity Analyst"],
        "best_certificates": ["AWS Solutions Architect", "CompTIA Security+", "Google IT Support"],
        "market_summary": "The tech market is aggressively shifting towards AI integration and Cloud Security. Focus on mastering Python and deploying secure cloud applications to remain highly competitive.",
        "youtube_queries": ["NetworkChuck IT Career", "freeCodeCamp Python", "AWS Solutions Architect roadmap"]
    }
