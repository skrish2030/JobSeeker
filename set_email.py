from backend.database import db

db.settings.update_one({'profile_id': 'global'}, {'$set': {
    'email_sender': 'skrish2030@gmail.com',
    'email_recipient': 'skrish2030@gmail.com',
    'email_smtp_server': 'smtp.gmail.com',
    'email_smtp_port': '587',
    'email_sender_password': 'nbvgmgtbiryvwmto'
}}, upsert=True)
print("Email settings updated successfully.")
