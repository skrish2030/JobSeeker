import re

with open('c:/Users/skris/OneDrive/Desktop/JobSeeker/backend/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("--- Authentication and Secret Key definition ---")
for line_no, line in enumerate(lines, 1):
    if "secret" in line.lower() or "jwt" in line.lower() or "token" in line.lower() or "auth" in line.lower():
        # filter out unrelated lines
        if any(w in line for w in ["def ", "class ", "token =", "SECRET =", "SECRET_KEY =", "JWT_"]):
            print(f"{line_no}: {line.strip()}")
        elif "dependencies=" in line or "security" in line or "authorize" in line:
            print(f"{line_no}: {line.strip()}")

print("\n--- Functions related to authentication/token ---")
current_func = None
func_lines = []
for line_no, line in enumerate(lines, 1):
    if line.startswith("def ") or line.startswith("async def "):
        if current_func:
            if any(k in current_func for k in ["auth", "token", "verify", "login", "register", "mfa"]):
                print(f"Function {current_func} (lines {func_start}-{line_no-1})")
        current_func = line.strip()
        func_start = line_no
if current_func and any(k in current_func for k in ["auth", "token", "verify", "login", "register", "mfa"]):
    print(f"Function {current_func} (lines {func_start}-{len(lines)})")
