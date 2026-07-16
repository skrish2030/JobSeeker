import re

with open("frontend/app.js", "r", encoding="utf-8") as file:
    content = file.read()

# find all occurrences of '/api/...'
matches = re.findall(r"'/api/[a-zA-Z0-9\-\_/]+'", content)
for m in sorted(list(set(matches))):
    print(m)
