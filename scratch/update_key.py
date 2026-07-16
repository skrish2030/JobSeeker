import sqlite3

DEFAULT_DB_PATH = r"C:\Users\skris\OneDrive\Desktop\JobSeeker\jobs.db"

def update_keys():
    print(f"Connecting to {DEFAULT_DB_PATH}")
    conn = sqlite3.connect(DEFAULT_DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE settings SET value = ? WHERE key = 'email_sender_password'", ('kowdzbyvitankbze',))
    conn.commit()
    conn.close()
    print('SMTP password updated successfully in master database.')

if __name__ == '__main__':
    update_keys()
