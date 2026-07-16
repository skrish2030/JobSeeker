with open('c:/Users/skris/OneDrive/Desktop/JobSeeker/frontend/app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_line = None
for line_no, line in enumerate(lines, 1):
    if "function renderJobList" in line:
        start_line = line_no
        break

if start_line:
    print(f"Found renderJobList at line {start_line}")
    for i in range(start_line-1, min(start_line + 80, len(lines))):
        print(f"{i+1}: {lines[i]}", end='')
else:
    print("renderJobList not found!")
