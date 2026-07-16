import sqlite3
import glob

db_files = glob.glob("C:/Users/skris/OneDrive/Desktop/JobSeeker/*.db")
print("User info in database files:")
for db in db_files:
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if cursor.fetchone():
            cursor.execute("SELECT id, username, email FROM users")
            users = cursor.fetchall()
            if users:
                print(f"{db}:")
                for u in users:
                    print(f"  - ID: {u[0]}, Username: {u[1]}, Email: {u[2]}")
        conn.close()
    except Exception as e:
         pass
