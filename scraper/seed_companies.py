import os
import sys

# Add project root to path to resolve backend/scraper imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import create_client, Client

def load_env_manually(filepath):
    """Fallback manual parser for .env files when python-dotenv is not installed."""
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip().strip('"').strip("'")
        except Exception as e:
            print(f"    [!] Failed to read {filepath} manually: {e}")

def get_supabase_client() -> Client:
    load_env_manually(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    load_env_manually(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend-next", ".env.local"))
    
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not key:
        url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
        key = os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")
        
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set.")
    return create_client(url, key)

def seed():
    print("=" * 60)
    print("   JOBSEEKER DATABASE SEEDER (TARGET COMPANIES)")
    print("=" * 60)
    
    try:
        supabase = get_supabase_client()
        print("[+] Supabase connection successful.")
    except Exception as e:
        print(f"[-] Database connection failed: {e}")
        return

    # Check if companies are already loaded
    try:
        res = supabase.table("companies").select("id").execute()
        count = len(res.data) if res.data else 0
        if count > 0:
            print(f"[!] The 'companies' table already contains {count} entries. Seeding skipped.")
            return
    except Exception as e:
        print(f"[-] Failed to query table status: {e}")
        return

    # List of default premium tech companies with their known Greenhouse/Lever/Ashby/Workday URLs
    default_companies = [
        # Greenhouse Portals
        {"name": "Stripe", "portal_url": "https://boards.greenhouse.io/stripe"},
        {"name": "Figma", "portal_url": "https://boards.greenhouse.io/figma"},
        {"name": "OpenAI", "portal_url": "https://boards.greenhouse.io/openai"},
        {"name": "Airbnb", "portal_url": "https://boards.greenhouse.io/airbnb"},
        {"name": "Retool", "portal_url": "https://boards.greenhouse.io/retool"},
        {"name": "Robinhood", "portal_url": "https://boards.greenhouse.io/robinhood"},
        {"name": "Scale AI", "portal_url": "https://boards.greenhouse.io/scaleai"},
        {"name": "Sentry", "portal_url": "https://boards.greenhouse.io/sentry"},
        {"name": "Rippling", "portal_url": "https://boards.greenhouse.io/rippling"},
        
        # Lever Portals
        {"name": "Netflix", "portal_url": "https://jobs.lever.co/netflix"},
        {"name": "Framer", "portal_url": "https://jobs.lever.co/framer"},
        {"name": "Lever", "portal_url": "https://jobs.lever.co/lever"},
        {"name": "Snyk", "portal_url": "https://jobs.lever.co/snyk"},
        {"name": "Postman", "portal_url": "https://jobs.lever.co/postman"},
        {"name": "Miro", "portal_url": "https://jobs.lever.co/miro"},
        
        # Ashby Portals
        {"name": "Vercel", "portal_url": "https://jobs.ashbyhq.com/vercel"},
        {"name": "Linear", "portal_url": "https://jobs.ashbyhq.com/linear"},
        {"name": "Ashby", "portal_url": "https://jobs.ashbyhq.com/ashby"},
        {"name": "Vantage", "portal_url": "https://jobs.ashbyhq.com/vantage"},
        
        # Workday Portals
        {"name": "Nvidia", "portal_url": "https://nvidia.myworkdayjobs.com/NVIDIAExternalCareerSite"},
        {"name": "Salesforce", "portal_url": "https://salesforce.myworkdayjobs.com/External_Career_Site"},
        {"name": "Adobe", "portal_url": "https://adobe.myworkdayjobs.com/external"}
    ]

    print(f"[*] Seeding {len(default_companies)} target tech companies into your Supabase database...")
    
    inserted_count = 0
    for comp in default_companies:
        try:
            supabase.table("companies").insert(comp).execute()
            print(f"  [+] Seeded: {comp['name']} ({comp['portal_url']})")
            inserted_count += 1
        except Exception as insert_err:
            print(f"  [-] Failed to insert {comp['name']}: {insert_err}")

    print("-" * 60)
    print(f"[+] Seeding complete! Seeded {inserted_count} / {len(default_companies)} companies successfully.")
    print("=" * 60)

if __name__ == "__main__":
    seed()
