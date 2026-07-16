import os
import re

backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
print(f"Scanning directory: {backend_dir} for any references to 'sqlite' or 'sqlite3'")

pattern = re.compile(r'sqlite', re.IGNORECASE)

found = False
for root, dirs, files in os.walk(backend_dir):
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                matches = pattern.findall(content)
                if matches:
                    print(f"Found in {path}: {len(matches)} times.")
                    found = True

if not found:
    print("No references to 'sqlite' found in Python files inside backend.")
