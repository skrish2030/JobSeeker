with open('c:/Users/skris/OneDrive/Desktop/JobSeeker/frontend/app.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

def print_function(name):
    start = None
    for line_no, line in enumerate(lines, 1):
        if f"async function {name}" in line or f"function {name}" in line:
            start = line_no
            break
    if start:
        print(f"\n--- Function {name} (starting at line {start}) ---")
        for i in range(start-1, min(start + 80, len(lines))):
            print(f"{i+1}: {lines[i]}", end='')
            if lines[i].startswith("}"):
                # simple heuristic to stop at end of function
                # but might stop early if there are nested blocks
                pass

print_function("loadInitialData")
print_function("fetchJobs")
print_function("fetchInterestedJobs")
