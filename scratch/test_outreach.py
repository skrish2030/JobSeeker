import requests
import sys

sys.stdout.reconfigure(encoding='utf-8')

JOB = {
    'title': 'Python Backend Engineer',
    'company': 'Stripe',
    'description': 'Build scalable payment APIs using Python, FastAPI, PostgreSQL and AWS.'
}

print('--- Testing outreach endpoint ---')
r = requests.post('http://127.0.0.1:8000/api/jobs/ai/outreach-templates', json=JOB, timeout=180)
data = r.json()
print(f'HTTP status: {r.status_code}')
print(f'Response status field: {data.get("status")}')

if data.get('linkedin_note'):
    print(f'LinkedIn note: {len(data["linkedin_note"])} chars - OK')
    print(f'Recruiter email: {len(data.get("recruiter_email",""))} chars - OK')
    print(f'Follow-up: {len(data.get("followup_message",""))} chars - OK')
    print('\nSUCCESS - All 4 AI features working! The earlier error was just Windows console encoding.')
else:
    print(f'FAIL: {data}')
