import boto3

def delete_all_users():
    try:
        dynamodb = boto3.resource("dynamodb")
        
        # 1. Delete all Users
        print("\n[1/4] Deleting all users from 'jobseeker_users'...")
        users_table = dynamodb.Table("jobseeker_users")
        scan = users_table.scan()
        count = 0
        for item in scan.get("Items", []):
            username = item.get("username")
            if username:
                users_table.delete_item(Key={"username": username})
                print(f"  - Deleted user: {username}")
                count += 1
        print(f"-> Successfully deleted {count} users.")

        # 2. Delete all Profiles (except 'global')
        print("\n[2/4] Deleting all user profiles (except global) from 'jobseeker_profiles'...")
        profiles_table = dynamodb.Table("jobseeker_profiles")
        scan = profiles_table.scan()
        count = 0
        for item in scan.get("Items", []):
            pid = item.get("profile_id")
            if pid and pid != "global":
                profiles_table.delete_item(Key={"profile_id": pid})
                print(f"  - Deleted profile: {pid}")
                count += 1
        print(f"-> Successfully deleted {count} profiles.")

        # 3. Delete all Sessions (session tokens, pending registrations, mfa codes)
        print("\n[3/4] Deleting all sessions from 'jobseeker_user_sessions'...")
        sessions_table = dynamodb.Table("jobseeker_user_sessions")
        scan = sessions_table.scan()
        count = 0
        for item in scan.get("Items", []):
            token = item.get("token")
            if token:
                sessions_table.delete_item(Key={"token": token})
                print(f"  - Deleted session/MFA token: {token}")
                count += 1
        print(f"-> Successfully deleted {count} session items.")

        # 4. Delete all Settings (except 'global')
        print("\n[4/4] Deleting all settings (except global) from 'jobseeker_settings'...")
        settings_table = dynamodb.Table("jobseeker_settings")
        scan = settings_table.scan()
        count = 0
        for item in scan.get("Items", []):
            pid = item.get("profile_id")
            if pid and pid != "global":
                settings_table.delete_item(Key={"profile_id": pid})
                print(f"  - Deleted settings for profile: {pid}")
                count += 1
        print(f"-> Successfully deleted {count} settings profiles.")

        print("\nDatabase reset complete! All user accounts have been successfully deleted.")
    except Exception as e:
        print(f"\n[ERROR] Failed to reset database: {e}")

if __name__ == "__main__":
    confirm = input("Are you sure you want to delete all user accounts, sessions, and settings? (y/N): ")
    if confirm.lower() == 'y':
        delete_all_users()
    else:
        print("Operation cancelled.")
