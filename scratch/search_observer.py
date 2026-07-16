import os

app_js_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "app.js")
with open(app_js_path, "r", encoding="utf-8") as f:
    content = f.read()

if "MutationObserver" in content:
    print("Found MutationObserver in app.js")
else:
    print("No MutationObserver found in app.js")
