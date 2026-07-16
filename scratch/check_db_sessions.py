import sqlite3

conn = sqlite3.connect('c:/Users/skris/OneDrive/Desktop/JobSeeker/jobs.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get list of tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row['name'] for row in cursor.fetchall()]
print(f"Tables in master DB: {tables}")

if 'users' in tables:
    cursor.execute("SELECT id, username, email FROM users;")
    print("\n--- Users ---")
    for row in cursor.fetchall():
        print(dict(row))

if 'user_sessions' in tables:
    cursor.execute("SELECT * FROM user_sessions;")
    print("\n--- Active Sessions ---")
    for row in cursor.fetchall():
        print(dict(row))

if 'mfa_codes' in tables:
    cursor.execute("SELECT * FROM mfa_codes;")
    print("\n--- MFA Codes ---")
    for row in cursor.fetchall():
        print(dict(row))

conn.close()
