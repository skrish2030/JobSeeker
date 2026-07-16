def print_lines(filename, start, end):
    print(f"\n=== {filename} lines {start}-{end} ===")
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for i in range(start-1, min(end, len(lines))):
        print(f"{i+1}: {lines[i]}", end='')

print_lines('c:/Users/skris/OneDrive/Desktop/JobSeeker/frontend/app.js', 95, 175)
print_lines('c:/Users/skris/OneDrive/Desktop/JobSeeker/frontend/app.js', 900, 950)
print_lines('c:/Users/skris/OneDrive/Desktop/JobSeeker/frontend/app.js', 70, 95)
print_lines('c:/Users/skris/OneDrive/Desktop/JobSeeker/frontend/app.js', 390, 420)
print_lines('c:/Users/skris/OneDrive/Desktop/JobSeeker/frontend/app.js', 600, 630)
