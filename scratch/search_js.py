with open('C:/Users/skris/OneDrive/Desktop/JobSeeker/frontend/app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'function apiRequest' in line or 'const apiRequest' in line or 'let apiRequest' in line:
        print(f"{i+1}: {line.strip()}")
