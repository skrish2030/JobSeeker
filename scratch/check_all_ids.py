import re
from bs4 import BeautifulSoup

with open('c:/Users/skris/OneDrive/Desktop/JobSeeker/frontend/app.js', 'r', encoding='utf-8') as f:
    js_content = f.read()

with open('c:/Users/skris/OneDrive/Desktop/JobSeeker/frontend/index.html', 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

# Regex to find document.getElementById('...') or document.getElementById("...")
ids = re.findall(r"document\.getElementById\(['\"]([^'\"]+)['\"]\)", js_content)
# Deduplicate
unique_ids = sorted(list(set(ids)))

print(f"Found {len(unique_ids)} unique IDs queried in app.js:")
missing_ids = []
for el_id in unique_ids:
    found = soup.find(id=el_id) is not None
    print(f"- {el_id}: {'FOUND' if found else 'NOT FOUND'}")
    if not found:
        missing_ids.append(el_id)

print(f"\nTotal missing IDs: {len(missing_ids)}")
print(f"Missing IDs: {missing_ids}")
