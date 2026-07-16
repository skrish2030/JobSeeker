import os
from supabase import create_client

def test():
    url = "https://fhbuvrzvgqorgwxeoyyh.supabase.co"
    key = ""
    env_path = r"C:\Users\skris\OneDrive\Desktop\JobSeeker\.env"
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith("SUPABASE_SERVICE_KEY="):
                    key = line.split("=", 1)[1].strip()

    if not key:
        print("Service key not found!")
        return

    supabase = create_client(url, key)
    try:
        res = supabase.auth.admin.get_user_by_id("3ab432d4-a25a-40ba-9d89-36b6d20f7932")
        print("Success!")
        print("User:", res.user)
        print("Email:", res.user.email)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test()
