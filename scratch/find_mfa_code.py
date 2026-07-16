import re

log_path = r"C:\Users\skris\.gemini\antigravity\brain\343b1e07-cd94-460b-aa2c-ed1275c0e158\.system_generated\tasks\task-4058.log"

with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

matches = re.findall(r"\[AUTH MFA\] Verification Code for saikrishna: (\d+)", content)
if matches:
    print(f"MFA Codes found: {matches}")
    print(f"Latest MFA Code: {matches[-1]}")
else:
    print("No MFA code found in the log yet.")
