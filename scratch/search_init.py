import re

with open('c:/Users/skris/OneDrive/Desktop/JobSeeker/frontend/app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("--- Calls to initializeProfiles ---")
for line_no, line in enumerate(lines, 1):
    if "initializeProfiles" in line:
        print(f"{line_no}: {line.strip()}")

print("\n--- DOMContentLoaded / window.onload / window.addEventListener ---")
for line_no, line in enumerate(lines, 1):
    if "DOMContentLoaded" in line or "onload" in line or "addEventListener" in line:
        # filter out simple field handlers
        if any(keyword in line for keyword in ["btn-", "click", "input", "submit", "change", "keydown", "mousedown"]):
            continue
        print(f"{line_no}: {line.strip()}")
