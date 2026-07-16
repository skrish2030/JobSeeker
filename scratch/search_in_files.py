import os

search_term = "/api/scrape/find"
frontend_dir = "frontend"

for root, dirs, files in os.walk(frontend_dir):
    for f in files:
        if f.endswith((".js", ".html", ".css")):
            path = os.path.join(root, f)
            try:
                with open(path, "r", encoding="utf-8") as file:
                    lines = file.readlines()
                for i, line in enumerate(lines):
                    if search_term in line:
                        print(f"{path}:{i+1}: {line.strip()}")
            except Exception as e:
                print(f"Error reading {path}: {e}")
