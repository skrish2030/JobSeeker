import sqlite3

conn = sqlite3.connect(r'C:\Users\skris\OneDrive\Desktop\JobSeeker\jobs.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()
c.execute("SELECT * FROM mfa_codes")
print([dict(r) for r in c.fetchall()])
conn.close()
