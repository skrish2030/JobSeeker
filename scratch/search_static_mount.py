with open('c:/Users/skris/OneDrive/Desktop/JobSeeker/backend/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("--- Searching StaticFiles in main.py ---")
for line_no, line in enumerate(lines, 1):
    if "StaticFiles" in line or "mount(" in line:
        print(f"{line_no}: {line.strip()}")
