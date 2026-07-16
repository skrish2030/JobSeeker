with open('c:/Users/skris/OneDrive/Desktop/JobSeeker/frontend/app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("--- Searching for DELETE target-companies in app.js ---")
for line_no, line in enumerate(lines, 1):
    if "/api/target-companies" in line and "DELETE" in line:
        print(f"{line_no}: {line.strip()}")
    elif "delete" in line.lower() and "company" in line.lower():
        print(f"{line_no}: {line.strip()}")
