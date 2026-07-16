import sqlite3
import requests
import json

def get_settings():
    try:
        conn = sqlite3.connect('jobs.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM settings")
        rows = cursor.fetchall()
        conn.close()
        return {row['key']: row['value'] for row in rows}
    except Exception as e:
        print(f"Error querying jobs.db: {e}")
        return {}

settings = get_settings()
api_key = settings.get('ai_api_key', '')
provider = settings.get('ai_provider', 'gemini')
model = settings.get('ai_model', 'gemini-1.5-flash')

print(f"Provider: {provider}")
print(f"Model: {model}")
print(f"API Key: {'configured' if api_key else 'empty'}")

if api_key:
    # Test list models
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        res = requests.get(url)
        if res.status_code == 200:
            models = res.json().get('models', [])
            print("\nAvailable models in Google AI Studio:")
            for m in models:
                name = m.get('name', '')
                if 'gemini' in name:
                    print(f"  - {name.replace('models/', '')} ({m.get('displayName', '')})")
        else:
            print(f"\nFailed to list models (status {res.status_code}): {res.text}")
    except Exception as e:
        print(f"\nError listing models: {e}")
else:
    print("\nNo Gemini API Key configured in master database.")
