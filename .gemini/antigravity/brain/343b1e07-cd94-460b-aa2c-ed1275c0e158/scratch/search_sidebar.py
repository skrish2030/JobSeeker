with open(r'c:\Users\skris\OneDrive\Desktop\JobSeeker\frontend\app.js', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        if 'sidebar-username' in line or 'Guest Session' in line or 'username' in line.lower():
            print(f"{i}: {line.strip()}")
