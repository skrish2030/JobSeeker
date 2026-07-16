import os
import re

filepath = r'c:\Users\skris\OneDrive\Desktop\JobSeeker\backend\ai_engine.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

ollama_helper = '''
def call_ollama_local(prompt, model="llama3", expect_json=True):
    url = "http://127.0.0.1:11434/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    if expect_json:
        payload["format"] = "json"
        
    try:
        response = requests.post(url, json=payload, timeout=120)
        if response.status_code == 200:
            res_data = response.json()
            response_text = res_data.get("response", "")
            if expect_json:
                if response_text.strip().startswith("```"):
                    response_text = re.sub(r"^```json\s*|```$", "", response_text.strip(), flags=re.MULTILINE)
                return json.loads(response_text.strip())
            return response_text
        else:
            logger.error(f"Ollama returned status {response.status_code}: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Failed to communicate with local Ollama: {str(e)}")
        return None

'''

# Inject helper
content = content.replace('def analyze_job_with_gemini', ollama_helper + 'def analyze_job_with_ollama')

# Rename functions
content = content.replace('analyze_job_with_gemini', 'analyze_job_with_ollama')
content = content.replace('generate_cv_tailoring_with_gemini', 'generate_cv_tailoring_with_ollama')
content = content.replace('generate_cover_letter_with_gemini', 'generate_cover_letter_with_ollama')
content = content.replace('generate_interview_prep_with_gemini', 'generate_interview_prep_with_ollama')
content = content.replace('generate_outreach_templates_with_gemini', 'generate_outreach_templates_with_ollama')

# Replace the network call in analyze_job_with_ollama
analyze_pattern = re.compile(r'    headers = {"Content-Type": "application/json"}.*?return None', re.DOTALL)

def replace_analyze(match):
    return '''    data = call_ollama_local(prompt, expect_json=True)
    if data:
        if "red_flags" in data and isinstance(data["red_flags"], list):
            data["red_flags"] = json.dumps(data["red_flags"])
        else:
            data["red_flags"] = "[]"
        return data
    return None'''

# Replace the network call in other functions
def replace_simple(match):
    success_status = '"status": "success", '
    fallback_return = match.group(1) # We can extract what the fallback returns if needed, but it's easier to just hardcode
    
    return '''    data = call_ollama_local(prompt, expect_json=True)
    if data:
        data["status"] = "success"
        return data
    return {
        "status": "error",
        "error": "Failed to communicate with local Ollama. Ensure it is running with 'ollama run llama3'."
    }'''

# Since regex is tricky over large blocks with varying fallback returns, we will just do string replacement for the request blocks.

# 1. analyze_job_with_ollama
content = re.sub(
    r'    headers = {"Content-Type": "application/json"}.*?        return None\n',
    r'''    data = call_ollama_local(prompt, expect_json=True)
    if data:
        if "red_flags" in data and isinstance(data["red_flags"], list):
            data["red_flags"] = json.dumps(data["red_flags"])
        else:
            data["red_flags"] = "[]"
        return data
    return None
''',
    content,
    count=1,
    flags=re.DOTALL
)

# 2. generate_cv_tailoring
content = re.sub(
    r'    headers = {"Content-Type": "application/json"}\n    payload = \{\n        "contents": \[\{"parts": \[\{"text": prompt\}\]\}\],\n        "generationConfig": \{"responseMimeType": "application/json"\}\n    \}\n    try:\n        response = requests\.post\(url, headers=headers, json=payload, timeout=15\)\n        if response\.status_code == 200:\n            res_data = response\.json\(\)\n            content_text = res_data\["candidates"\]\[0\]\["content"\]\["parts"\]\[0\]\["text"\]\n            if content_text\.strip\(\)\.startswith\("```"\):\n                content_text = re\.sub\(r"\^```json\\s\*\|```\$", "", content_text\.strip\(\), flags=re\.MULTILINE\)\n            data = json\.loads\(content_text\.strip\(\)\)\n            return \{"status": "success", "tips": data\.get\("tips", \[\]\)\}\n    except Exception as e:\n        logger\.error\(f"Failed to generate CV tailoring: \{str\(e\)\}"\)\n    return \{\n        "status": "error",\n        "tips": \["Could not communicate with Gemini\. Please check your API key in the configuration console\."\]\n    \}',
    r'''    data = call_ollama_local(prompt, expect_json=True)
    if data:
        return {"status": "success", "tips": data.get("tips", [])}
    return {"status": "error", "tips": ["Could not communicate with local Ollama."]}''',
    content
)

# 3. generate_cover_letter
content = re.sub(
    r'    headers = {"Content-Type": "application/json"}\n    payload = \{\n        "contents": \[\{"parts": \[\{"text": prompt\}\]\}\],\n        "generationConfig": \{"responseMimeType": "application/json"\}\n    \}\n    try:\n        response = requests\.post\(url, headers=headers, json=payload, timeout=15\)\n        if response\.status_code == 200:\n            res_data = response\.json\(\)\n            content_text = res_data\["candidates"\]\[0\]\["content"\]\["parts"\]\[0\]\["text"\]\n            if content_text\.strip\(\)\.startswith\("```"\):\n                content_text = re\.sub\(r"\^```json\\s\*\|```\$", "", content_text\.strip\(\), flags=re\.MULTILINE\)\n            data = json\.loads\(content_text\.strip\(\)\)\n            return \{"status": "success", "cover_letter": data\.get\("cover_letter", ""\)\}\n    except Exception as e:\n        logger\.error\(f"Failed to generate cover letter: \{str\(e\)\}"\)\n    return \{\n        "status": "error",\n        "cover_letter": "Failed to communicate with Gemini\. Please check your API key in settings\."\n    \}',
    r'''    data = call_ollama_local(prompt, expect_json=True)
    if data:
        return {"status": "success", "cover_letter": data.get("cover_letter", "")}
    return {"status": "error", "cover_letter": "Failed to communicate with local Ollama."}''',
    content
)

# 4. generate_interview_prep
content = re.sub(
    r'    headers = {"Content-Type": "application/json"}\n    payload = \{\n        "contents": \[\{"parts": \[\{"text": prompt\}\]\}\],\n        "generationConfig": \{"responseMimeType": "application/json"\}\n    \}\n    try:\n        response = requests\.post\(url, headers=headers, json=payload, timeout=15\)\n        if response\.status_code == 200:\n            res_data = response\.json\(\)\n            content_text = res_data\["candidates"\]\[0\]\["content"\]\["parts"\]\[0\]\["text"\]\n            if content_text\.strip\(\)\.startswith\("```"\):\n                content_text = re\.sub\(r"\^```json\\s\*\|```\$", "", content_text\.strip\(\), flags=re\.MULTILINE\)\n            data = json\.loads\(content_text\.strip\(\)\)\n            return \{"status": "success", "qa": data\.get\("qa", \[\]\)\}\n    except Exception as e:\n        logger\.error\(f"Failed to generate interview prep Q&A: \{str\(e\)\}"\)\n    return \{\n        "status": "error",\n        "qa": \[\{"question": "Error", "answer": "Could not connect to Gemini\. Check your API key\."\}\]\n    \}',
    r'''    data = call_ollama_local(prompt, expect_json=True)
    if data:
        return {"status": "success", "qa": data.get("qa", [])}
    return {"status": "error", "qa": [{"question": "Error", "answer": "Could not connect to local Ollama."}]}''',
    content
)

# 5. generate_outreach_templates
content = re.sub(
    r'    headers = {"Content-Type": "application/json"}.*?return \{\n        "status": "error",\n        "linkedin_note": "Failed to generate\.",\n        "recruiter_email": "Failed to generate\.",\n        "followup_message": "Failed to generate\."\n    \}',
    r'''    data = call_ollama_local(prompt, expect_json=True)
    if data:
        return {
            "status": "success",
            "linkedin_note": data.get("linkedin_note", ""),
            "recruiter_email": data.get("recruiter_email", ""),
            "followup_message": data.get("followup_message", "")
        }
    return {
        "status": "error",
        "linkedin_note": "Failed to communicate with local Ollama.",
        "recruiter_email": "Failed to communicate with local Ollama.",
        "followup_message": "Failed to communicate with local Ollama."
    }''',
    content,
    flags=re.DOTALL
)

# Strip out url = "https://generativelanguage..."
content = re.sub(r'    url = f"https://generativelanguage.*?\\n', '', content)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Migration to Ollama completed successfully.")
