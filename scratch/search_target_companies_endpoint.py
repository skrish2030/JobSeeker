with open('c:/Users/skris/OneDrive/Desktop/JobSeeker/backend/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("--- Searching target-companies in main.py ---")
start_line = None
for line_no, line in enumerate(lines, 1):
    if "/api/target-companies" in line:
        start_line = line_no
        break

if start_line:
    print(f"Found target-companies endpoint around line {start_line}")
    for i in range(start_line-5, min(start_line + 45, len(lines))):
        print(f"{i+1}: {lines[i]}", end='')
else:
    print("target-companies endpoint not found!")
