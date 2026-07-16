import os

query = "Generation failed"
for root, dirs, files in os.walk('.'):
    # Skip virtual environments and hidden directories
    if any(p in root for p in ['.venv', 'node_modules', '.git', '.terraform']):
        continue
    for file in files:
        if file.endswith(('.py', '.js', '.jsx', '.ts', '.tsx', '.html', '.json')):
            path = os.path.join(root, file)
            try:
                with open(path, encoding='utf-8', errors='ignore') as f:
                    for i, line in enumerate(f):
                        if query in line:
                            print(f"{path}: Line {i+1}: {line.strip()}")
            except Exception:
                pass
