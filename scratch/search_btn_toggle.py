with open("frontend/app.js", "r", encoding="utf-8") as file:
    content = file.readlines()

for i, line in enumerate(content):
    if "btn-toggle-analytics" in line or "btnToggleAnalytics" in line:
        print(f"Line {i+1}: {line.strip()}")
