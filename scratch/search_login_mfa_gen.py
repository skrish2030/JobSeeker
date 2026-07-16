with open('c:/Users/skris/OneDrive/Desktop/JobSeeker/backend/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_line = None
for line_no, line in enumerate(lines, 1):
    if "def api_login" in line:
        start_line = line_no
        break

if start_line:
    print(f"Found api_login around line {start_line}")
    for i in range(start_line-1, min(start_line + 50, len(lines))):
        print(f"{i+1}: {lines[i]}", end='')
else:
    print("api_login not found!")
