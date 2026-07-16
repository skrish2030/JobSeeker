with open('c:/Users/skris/OneDrive/Desktop/JobSeeker/backend/database.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("--- Searching get_target_companies in database.py ---")
start_line = None
for line_no, line in enumerate(lines, 1):
    if "def get_target_companies" in line:
        start_line = line_no
        break

if start_line:
    print(f"Found get_target_companies around line {start_line}")
    for i in range(start_line-1, min(start_line + 25, len(lines))):
        print(f"{i+1}: {lines[i]}", end='')
else:
    print("get_target_companies not found!")
