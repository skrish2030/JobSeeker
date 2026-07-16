from backend.database import db

sender = "skrish2050@gmail.com"
password = "nbvgmgtbiryvwmto"
recipient = "skrish2030@gmail.com"

db.settings.update_many({}, {"$set": {
    "email_sender": sender,
    "email_sender_password": password,
    "email_recipient": recipient,
    "email_smtp_server": "smtp.gmail.com",
    "email_smtp_port": "587"
}})

print("Correct credentials synced to all profiles in database!")
