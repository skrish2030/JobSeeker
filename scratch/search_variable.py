with open('c:/Users/skris/OneDrive/Desktop/JobSeeker/frontend/app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

vars_to_search = ['btnSettings', 'settingsClose', 'tabButtons']
print("--- Searching variables in app.js ---")
for var in vars_to_search:
    print(f"\nUsages of: {var}")
    for line_no, line in enumerate(lines, 1):
        if var in line:
            print(f"{line_no}: {line.strip()}")
