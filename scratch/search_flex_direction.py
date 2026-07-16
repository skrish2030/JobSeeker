with open('c:/Users/skris/OneDrive/Desktop/JobSeeker/frontend/styles.css', 'r', encoding='utf-8') as f:
    css = f.read()

lines = css.splitlines()
print("--- Searching flex-direction in styles.css ---")
for line_no, line in enumerate(lines, 1):
    if "flex-direction" in line:
        print(f"{line_no}: {line.strip()}")
        # print selector context
        for idx in range(max(0, line_no - 3), line_no):
            print(f"  {idx+1}: {lines[idx]}")
