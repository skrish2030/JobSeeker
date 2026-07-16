import sqlite3
import os

def inspect_db(filepath):
    if not os.path.exists(filepath):
        print(f"[-] File not found: {filepath}")
        return
        
    print(f"\n[*] Inspecting local SQLite database: {filepath}")
    try:
        conn = sqlite3.connect(filepath)
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            print("  No tables found.")
            return
            
        for t in tables:
            table_name = t[0]
            cursor.execute(f"SELECT count(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"  Table: '{table_name}' - {count} rows")
            
            # Print columns
            cursor.execute(f"PRAGMA table_info({table_name});")
            cols = [c[1] for c in cursor.fetchall()]
            print(f"    Columns: {', '.join(cols)}")
            
        conn.close()
    except Exception as e:
        print(f"  Error: {e}")

if __name__ == "__main__":
    db_paths = [
        r"C:\Users\skris\OneDrive\Desktop\JobSeeker\jobs.db",
        r"C:\Users\skris\OneDrive\Desktop\JobSeeker\jobs_c209528e-d742-4088-95e1-e387b5895f01_default.db",
        r"C:\Users\skris\OneDrive\Desktop\JobSeeker\d98e5c12-179c-4f99-95a3-a89a95ff4964_jobs.db"
    ]
    for path in db_paths:
        inspect_db(path)
