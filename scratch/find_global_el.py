with open('c:/Users/skris/OneDrive/Desktop/JobSeeker/frontend/app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("--- Global document.getElement / querySelector ---")
in_function = False
brace_count = 0
for line_no, line in enumerate(lines, 1):
    stripped = line.strip()
    # Track curly braces to know if we are inside a function/class
    # (very simple heuristic)
    if 'function' in line or '=>' in line or 'class' in line:
        in_function = True
    
    # Simple brace matching
    brace_count += line.count('{') - line.count('}')
    if brace_count <= 0:
        in_function = False
        
    if not in_function:
        if "document.get" in line or "document.query" in line:
            print(f"{line_no}: {stripped}")
