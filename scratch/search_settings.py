import os

def search_files(query):
    for fn in ['backend/database.py', 'backend/main.py', 'backend/ai_engine.py']:
        if os.path.exists(fn):
            with open(fn, encoding='utf-8') as f:
                for i, line in enumerate(f):
                    if query.lower() in line.lower():
                        print(f"{fn}: Line {i+1}: {line.strip()}")

print("--- AI_API_KEY search ---")
search_files("ai_api_key")
print("\n--- SETTINGS search ---")
search_files("settings")
