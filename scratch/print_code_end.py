def print_lines(filename, start, end):
    print(f"\n=== {filename} lines {start}-{end} ===")
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    print(f"Total lines: {len(lines)}")
    for i in range(start-1, min(end, len(lines))):
        print(f"{i+1}: {lines[i]}", end='')

with open('c:/Users/skris/OneDrive/Desktop/JobSeeker/frontend/app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()
total = len(lines)
print_lines('c:/Users/skris/OneDrive/Desktop/JobSeeker/frontend/app.js', max(1, total - 200), total)
