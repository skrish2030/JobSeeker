import sys
sys.path.append("C:/Users/skris/OneDrive/Desktop/JobSeeker")

from backend.database import get_jobs, active_user_id_var, active_profile_id_var

# Set context
u_tok = active_user_id_var.set("global")
p_tok = active_profile_id_var.set("default")

try:
    jobs = get_jobs()
    print(f"Number of jobs returned by get_jobs(): {len(jobs)}")
finally:
    active_user_id_var.reset(u_tok)
    active_profile_id_var.reset(p_tok)
