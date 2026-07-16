import requests

BASE_URL = 'http://127.0.0.1:8000'

# Step 1: Login
login_payload = {
    "username": "saikrishna",
    "password": "Kittu!!09"
}
print(f"Logging in with: {login_payload}")
r = requests.post(f"{BASE_URL}/api/auth/login", json=login_payload)
print(f"Login response status: {r.status_code}")
print(f"Login response body: {r.json()}")

# If it requires MFA, it will print mfa_required. Let's see.
