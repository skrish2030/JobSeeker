with open('c:/Users/skris/OneDrive/Desktop/JobSeeker/frontend/app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("--- Searching tab-panel in app.js ---")
for line_no, line in enumerate(lines, 1):
    if "tab-panel" in line or "panel-" in line:
        print(f"{line_no}: {line.strip()}")
