import sqlite3
import glob
import os

db_files = glob.glob("C:/Users/skris/OneDrive/Desktop/JobSeeker/*.db")
print("Found database files:")
for db in db_files:
    size = os.path.getsize(db) / (1024 * 1024)
    print(f"{os.path.basename(db)}: {size:.2f} MB")
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cursor.fetchall()]
        print(f"  Tables: {tables}")
        if "jobs" in tables:
            cursor.execute("SELECT count(*) FROM jobs")
            cnt = cursor.fetchone()[0]
            print(f"  Jobs count: {cnt}")
        conn.close()
    except Exception as e:
        print(f"  Error reading {db}: {e}")
