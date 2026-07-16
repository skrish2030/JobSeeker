with open('c:/Users/skris/OneDrive/Desktop/JobSeeker/frontend/styles.css', 'r', encoding='utf-8') as f:
    css = f.read()

keywords = ['search-bar', 'search-panel', 'header-search', 'btn-find', 'panel-header', 'tab-panel', 'display:', 'visibility:']
lines = css.splitlines()

print("--- CSS rules containing layout/display/visibility keyword search ---")
for line_no, line in enumerate(lines, 1):
    if any(k in line for k in keywords):
        print(f"{line_no}: {line.strip()}")
