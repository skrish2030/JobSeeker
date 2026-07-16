import sys
import os
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Set AWS environment variables for testing (mock profile/region if needed)
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
os.environ["DYNAMODB_JOBS_TABLE"] = "jobseeker_jobs"

from backend.database import get_jobs

print("Testing get_jobs() from database...")
try:
    # Try empty search
    jobs = get_jobs()
    print(f"Empty search returned {len(jobs)} jobs.")
    
    # Try keyword search
    jobs_sre = get_jobs(filters={"search": "site reliability engineer"})
    print(f"SRE search returned {len(jobs_sre)} jobs.")
except Exception as e:
    import traceback
    print("Error occurred:")
    traceback.print_exc()
