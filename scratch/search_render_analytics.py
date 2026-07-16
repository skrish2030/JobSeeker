with open("frontend/app.js", "r", encoding="utf-8") as file:
    content = file.readlines()

for i, line in enumerate(content):
    if "renderAnalytics" in line or "analytics-panel-container" in line:
        print(f"Line {i+1}: {line.strip()}")
