from pymongo import MongoClient

client = MongoClient('mongodb://mongodb:27017/')
db = client.jobseeker

smtp_settings = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": "587",
    "smtp_username": "skrish2050@gmail.com",
    "smtp_password": "nbvgmgtbiryvwmto"
}

db.settings.update_one(
    {"_id": "global_settings"},
    {"$set": smtp_settings},
    upsert=True
)
print("Successfully updated SMTP settings in the database.")
