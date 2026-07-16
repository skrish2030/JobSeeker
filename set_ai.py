from pymongo import MongoClient

client = MongoClient('mongodb://mongodb:27017/')
db = client.jobseeker

ai_settings = {
    "ai_provider": "gemini",
    "ai_model": "gemini-2.0-flash", # keeping it modern and fast
    "ai_api_key": "AQ.Ab8RN6JG43dX7ZEOJwB34y5eIVjRWL8IZE3MDRPYl3TUjpJ0YA"
}

db.settings.update_one(
    {"_id": "global_settings"},
    {"$set": ai_settings},
    upsert=True
)
print("Successfully updated Gemini API settings in the database.")
