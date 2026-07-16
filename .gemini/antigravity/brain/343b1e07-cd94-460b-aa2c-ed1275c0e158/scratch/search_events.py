with open(r'c:\Users\skris\OneDrive\Desktop\JobSeeker\frontend\app.js', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        if 'btn-find-jobs' in line or 'setupEventListeners' in line:
            print(f"{i}: {line.strip()}")
