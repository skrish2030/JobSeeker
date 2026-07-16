with open("C:/Users/skris/OneDrive/Desktop/JobSeeker/backend/ai_engine.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "def generate_cv_tailoring_with_ai" in line or "def generate_cover_letter_with_ai" in line:
        print(f"Line {i+1}: {line.strip()}")
