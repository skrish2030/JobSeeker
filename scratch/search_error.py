import os

query = "Generation failed"
for root, dirs, files in os.walk('backend'):
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            with open(path, encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f):
                    if query in line:
                        print(f"{path}: Line {i+1}: {line.strip()}")
