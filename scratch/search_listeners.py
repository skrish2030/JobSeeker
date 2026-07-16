import os

app_js_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "app.js")
with open(app_js_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines, 1):
    if "addEventListener" in line:
        print(f"Line {idx}: {line.strip()}")
