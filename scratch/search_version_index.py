with open('c:/Users/skris/OneDrive/Desktop/JobSeeker/frontend/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("--- Searching version query parameters in index.html ---")
for line_no, line in enumerate(lines, 1):
    if "?v=" in line:
        print(f"{line_no}: {line.strip()}")
