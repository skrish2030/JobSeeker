import re

with open('c:/Users/skris/OneDrive/Desktop/JobSeeker/frontend/app.js', 'r', encoding='utf-8') as f:
    content = f.read()

print(f"Total size of app.js: {len(content)} characters")

# Find references to "Guest Session" or "sidebar-username"
print("\n--- Search for sidebar-username or Guest Session ---")
for line_no, line in enumerate(content.splitlines(), 1):
    if "sidebar-username" in line or "Guest Session" in line or "guest" in line.lower():
        print(f"{line_no}: {line.strip()}")

# Find references to auth logic, token, login, logout, refresh, localStorage, sessionStorage
print("\n--- LocalStorage/SessionStorage usages ---")
for line_no, line in enumerate(content.splitlines(), 1):
    if "localStorage" in line or "sessionStorage" in line:
        print(f"{line_no}: {line.strip()}")

# Find references to settings
print("\n--- References to settings or panel-settings ---")
for line_no, line in enumerate(content.splitlines(), 1):
    if "panel-settings" in line or "settings-nav" in line or "btn-settings" in line:
        print(f"{line_no}: {line.strip()}")

# Find references to search/find jobs or "btn-find-jobs"
print("\n--- References to search buttons/inputs ---")
for line_no, line in enumerate(content.splitlines(), 1):
    if "btn-find-jobs" in line or "header-search-input" in line or "header-location-input" in line:
        print(f"{line_no}: {line.strip()}")
