import os

index_html_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "index.html")
with open(index_html_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines, 1):
    if "analytics-panel-container" in line or "scheduler-viz-container" in line:
        print(f"Line {idx}: {line.strip()}")
