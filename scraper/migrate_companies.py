import os
import sys
import sqlite3

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

def migrate():
    print("=" * 60)
    print("   JOBSEEKER LOCAL SQLITE TO SUPABASE MIGRATION TOOL")
    print("=" * 60)
    
    sqlite_path = r"C:\Users\skris\OneDrive\Desktop\JobSeeker\jobs_c209528e-d742-4088-95e1-e387b5895f01_default.db"
    if not os.path.exists(sqlite_path):
        print(f"[-] SQLite database not found at: {sqlite_path}")
        return
        
    try:
        supabase = get_supabase_client()
        print("[+] Supabase connection successful.")
    except Exception as e:
        print(f"[-] Database connection failed: {e}")
        return

    # 1. Fetch companies from local SQLite database
    print(f"[*] Reading companies from SQLite: {sqlite_path}...")
    local_companies = []
    try:
        conn = sqlite3.connect(sqlite_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name, portal_url FROM target_companies;")
        rows = cursor.fetchall()
        for r in rows:
            name = r[0]
            url = r[1]
            if name and name.strip():
                local_companies.append({
                    "name": name.strip(),
                    "portal_url": url.strip() if url else None
                })
        conn.close()
        print(f"[+] Read {len(local_companies)} companies from local database.")
    except Exception as e:
        print(f"[-] SQLite read failed: {e}")
        return

    if not local_companies:
        print("[-] No companies to migrate.")
        return

    # 2. De-duplicate locally by company name (case-insensitive deduplication)
    seen = {}
    deduped_companies = []
    for c in local_companies:
        name_lower = c["name"].lower()
        if name_lower not in seen:
            seen[name_lower] = True
            deduped_companies.append(c)
    print(f"[+] Deduplicated locally down to {len(deduped_companies)} unique companies.")

    # 3. Bulk upload in batches to Supabase to prevent size limits
    batch_size = 500
    total_companies = len(deduped_companies)
    inserted_count = 0
    
    print(f"[*] Migrating {total_companies} companies to Supabase in batches of {batch_size}...")
    
    for i in range(0, total_companies, batch_size):
        batch = deduped_companies[i:i+batch_size]
        print(f"  Uploading batch {i//batch_size + 1} ({len(batch)} companies)...")
        try:
            # Upsert will override existing or insert new without throwing unique constraint failures!
            supabase.table("companies").upsert(batch, on_conflict="name").execute()
            inserted_count += len(batch)
        except Exception as batch_err:
            # If batch upsert fails (e.g. if one URL format is invalid, we can insert row-by-row as fallback)
            print(f"  [!] Batch upsert failed: {batch_err}. Falling back to row-by-row insert for this batch...")
            for comp in batch:
                try:
                    supabase.table("companies").upsert(comp, on_conflict="name").execute()
                    inserted_count += 1
                except Exception as row_err:
                    pass # Ignore row-level failures (duplicates/nulls)

    print("-" * 60)
    print(f"[+] Migration complete! Successfully loaded {inserted_count} / {total_companies} companies into Supabase.")
    print("=" * 60)

if __name__ == "__main__":
    migrate()
