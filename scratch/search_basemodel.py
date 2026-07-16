with open('c:/Users/skris/OneDrive/Desktop/JobSeeker/backend/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("--- Searching BaseModel in main.py ---")
for line_no, line in enumerate(lines, 1):
    if "BaseModel" in line:
        print(f"{line_no}: {line.strip()}")
