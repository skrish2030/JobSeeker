def print_lines(filename, start, end):
    print(f"\n=== {filename} lines {start}-{end} ===")
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for i in range(start-1, min(end, len(lines))):
        print(f"{i+1}: {lines[i]}", end='')

print_lines('c:/Users/skris/OneDrive/Desktop/JobSeeker/backend/main.py', 110, 140)
