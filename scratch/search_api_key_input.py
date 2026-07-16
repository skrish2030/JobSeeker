with open("frontend/index.html", "r", encoding="utf-8") as file:
    content = file.readlines()

for i, line in enumerate(content):
    if "gemini" in line.lower() or "smtp" in line.lower() or "password" in line.lower():
        print(f"Line {i+1}: {line.strip()}")
