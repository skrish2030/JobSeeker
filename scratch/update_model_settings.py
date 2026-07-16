import sqlite3, glob

DBS = ["jobs.db"] + list(glob.glob("jobs_*.db"))

for db_file in DBS:
    try:
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()
        updates = [
            ("interview_llm_model", "llama3.2:3b"),
            ("interview_llm_provider", "ollama"),
            ("interview_llm_api_base", "http://localhost:11434/v1"),
            ("interview_llm_api_key", ""),
        ]
        for key, val in updates:
            cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, val))
        conn.commit()
        conn.close()
        print(f"OK: {db_file}")
    except Exception as e:
        print(f"Skip {db_file}: {e}")

print("Done!")
