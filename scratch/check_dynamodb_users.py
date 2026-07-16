import boto3
import json

try:
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    table = dynamodb.Table("jobseeker_users")
    
    print("Scanning DynamoDB table 'jobseeker_users'...")
    response = table.scan()
    items = response.get("Items", [])
    
    if not items:
        print("No users found in DynamoDB table 'jobseeker_users'.")
    else:
        print(f"\nFound {len(items)} users in DynamoDB:")
        for idx, item in enumerate(items, 1):
            print(f"  {idx}. Username: {item.get('username')} | Email: {item.get('email')} | User ID: {item.get('id')}")
            
except Exception as e:
    print(f"Error reading DynamoDB table: {e}")
