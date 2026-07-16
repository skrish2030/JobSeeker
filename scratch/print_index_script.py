def print_lines(filename, start, end):
    print(f"\n=== {filename} lines {start}-{end} ===")
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for i in range(start-1, min(end, len(lines))):
        print(f"{i+1}: {lines[i]}", end='')

with open('c:/Users/skris/OneDrive/Desktop/JobSeeker/frontend/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()
total = len(lines)
print_lines('c:/Users/skris/OneDrive/Desktop/JobSeeker/frontend/index.html', max(1, total - 40), total)
