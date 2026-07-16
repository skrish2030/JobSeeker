import sys
import re

filepath = r"C:\Users\skris\OneDrive\Desktop\JobSeeker\backend\main.py"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Remove boto3 and mangum imports
content = re.sub(r"^import boto3\n", "", content, flags=re.MULTILINE)
content = re.sub(r"^from mangum import Mangum\n^handler = Mangum\(app\)\n?", "", content, flags=re.MULTILINE)

# 2. Fix the imports from database.py
content = re.sub(r"dynamodb,\s*DYNAMODB_SESSIONS_TABLE", "db", content)
content = re.sub(r",\s*DYNAMODB_COMPANIES_TABLE", "", content)

# 3. Fix is_username_available
old_is_username_available = """    sessions_table = dynamodb.Table(DYNAMODB_SESSIONS_TABLE)
    try:
        res = sessions_table.scan(
            FilterExpression=boto3.dynamodb.conditions.Attr("token").begins_with("pending_") & 
                             boto3.dynamodb.conditions.Attr("username").eq(username)
        )
        if res.get("Items"):
            return False
    except Exception as e:
        logger.error(f"Error checking pending registrations: {e}")"""
        
new_is_username_available = """    from backend.database import db
    try:
        if db.sessions.find_one({"token": {"$regex": "^pending_"}, "username": username}):
            return False
    except Exception as e:
        logger.error(f"Error checking pending registrations: {e}")"""
        
content = content.replace(old_is_username_available, new_is_username_available)

# 4. Fix api_register_verify batch write
old_batch = """            companies_table = dynamodb.Table(DYNAMODB_COMPANIES_TABLE)
            key = f"{user_id}_default"
            added_at = datetime.now().isoformat()
            
            with companies_table.batch_writer() as batch:
                for comp in master_companies:
                    p_url = comp.get("portal_url")
                    item = {
                        "profile_id": key,
                        "company_name": comp["name"].strip(),
                        "portal_url": p_url.strip() if p_url else None,
                        "added_at": added_at
                    }
                    batch.put_item(Item=item)"""
                    
new_batch = """            from backend.database import db
            key = f"{user_id}_default"
            added_at = datetime.now().isoformat()
            
            for comp in master_companies:
                p_url = comp.get("portal_url")
                item = {
                    "profile_id": key,
                    "company_name": comp["name"].strip(),
                    "portal_url": p_url.strip() if p_url else None,
                    "added_at": added_at
                }
                db.companies.insert_one(item)"""

content = content.replace(old_batch, new_batch)

# 5. Fix IS_LAMBDA references since we set it to False in database.py
content = re.sub(r"from backend.database import IS_LAMBDA\n", "", content)
content = re.sub(r"from backend.database import (\s*init_db)", r"from backend.database import \1", content)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("main.py updated successfully.")
