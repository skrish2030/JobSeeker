with open("frontend/styles.css", "r", encoding="utf-8") as file:
    content = file.readlines()

for i, line in enumerate(content):
    if "pulse" in line.lower() or "keyframes" in line.lower():
        print(f"Line {i+1}: {line.strip()}")
