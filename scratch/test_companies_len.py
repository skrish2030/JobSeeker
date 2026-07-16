import sys
sys.path.append("C:/Users/skris/OneDrive/Desktop/JobSeeker")

from backend.database import get_target_companies, active_user_id_var, active_profile_id_var

# Set context
u_tok = active_user_id_var.set("e2f9bcc0-8170-4742-a1ea-4f65636bb61b")
p_tok = active_profile_id_var.set("default")

try:
    companies = get_target_companies()
    print(f"Number of companies returned: {len(companies)}")
finally:
    active_user_id_var.reset(u_tok)
    active_profile_id_var.reset(p_tok)
