import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "jobs.db")

print(f"Checking SQLite database at: {db_path}")
if not os.path.exists(db_path):
    print("Database file does not exist locally.")
else:
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        table_exists = cursor.fetchone()
        if not table_exists:
            print("Table 'users' does not exist in the database.")
        else:
            cursor.execute("SELECT id, username, email, created_at FROM users")
            users = cursor.fetchall()
            print(f"\nFound {len(users)} users:")
            print("-" * 60)
            for user in users:
                print(f"ID: {user['id']}")
                print(f"Username: {user['username']}")
                print(f"Email: {user['email']}")
                print(f"Created At: {user['created_at']}")
                print("-" * 60)
        conn.close()
    except Exception as e:
        print(f"Error querying database: {e}")
