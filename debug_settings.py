from backend.database import db
for doc in db.settings.find():
    print(f"Profile: {doc.get('profile_id')}")
    print(f"Sender: {doc.get('email_sender')}")
    print(f"Password: {doc.get('email_sender_password')}")
    print('---')
