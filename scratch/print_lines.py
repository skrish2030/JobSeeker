with open("C:/Users/skris/OneDrive/Desktop/JobSeeker/backend/ai_engine.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx in range(211, 387):
    if idx < len(lines):
        print(f"Line {idx+1}: {lines[idx]}", end="")
