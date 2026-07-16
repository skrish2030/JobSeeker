with open('c:/Users/skris/OneDrive/Desktop/JobSeeker/frontend/app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for line_no, line in enumerate(lines, 1):
    if "async function initializeProfiles" in line:
        print(f"Found at line {line_no}: {line.strip()}")
        # print context
        for idx in range(max(0, line_no - 2), min(len(lines), line_no + 25)):
            print(f"{idx+1}: {lines[idx]}", end='')
