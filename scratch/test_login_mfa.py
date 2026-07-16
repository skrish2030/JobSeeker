import requests

BASE_URL = 'http://127.0.0.1:8000'

# Step 2: Verify MFA
mfa_payload = {
    "username": "saikrishna",
    "code": "589610"
}
print(f"Verifying MFA with: {mfa_payload}")
r = requests.post(f"{BASE_URL}/api/auth/mfa", json=mfa_payload)
print(f"MFA response status: {r.status_code}")
res_body = r.json()
print(f"MFA response body: {res_body}")

if r.status_code == 200 and 'token' in res_body:
    token = res_body['token']
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Profile-Id": "default"
    }
    
    # Try fetching settings
    r_settings = requests.get(f"{BASE_URL}/api/settings", headers=headers)
    print(f"Settings response status: {r_settings.status_code}")
    print(f"Settings response body: {r_settings.json()}")
    
    # Try fetching target companies
    r_companies = requests.get(f"{BASE_URL}/api/target-companies", headers=headers)
    print(f"Companies response status: {r_companies.status_code}")
    print(f"Companies response body: {len(r_companies.json())} companies found")
    
    # Try fetching jobs
    r_jobs = requests.get(f"{BASE_URL}/api/jobs", headers=headers)
    print(f"Jobs response status: {r_jobs.status_code}")
    print(f"Jobs found: {len(r_jobs.json())}")
