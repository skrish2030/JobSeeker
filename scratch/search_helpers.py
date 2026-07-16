with open('c:/Users/skris/OneDrive/Desktop/JobSeeker/frontend/app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("--- Searching for escapeHTML and formatDate ---")
for line_no, line in enumerate(lines, 1):
    if "function escapeHTML" in line or "function formatDate" in line:
        print(f"{line_no}: {line.strip()}")
