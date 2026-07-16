with open("C:/Users/skris/OneDrive/Desktop/JobSeeker/frontend/styles.css", "r", encoding="utf-8") as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")
for idx in range(len(lines) - 200, len(lines)):
    print(f"Line {idx+1}: {lines[idx]}", end="")
