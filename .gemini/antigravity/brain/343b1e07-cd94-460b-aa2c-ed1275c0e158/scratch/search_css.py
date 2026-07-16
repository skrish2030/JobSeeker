with open(r'c:\Users\skris\OneDrive\Desktop\JobSeeker\frontend\styles.css', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        if 'panel-header-search' in line or 'search-panel-inline' in line or 'display: none' in line:
            print(f"{i}: {line.strip()}")
