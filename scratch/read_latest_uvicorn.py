log_path = r"C:\Users\skris\.gemini\antigravity\brain\343b1e07-cd94-460b-aa2c-ed1275c0e158\.system_generated\tasks\task-4058.log"

with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")
print("--- Last 100 lines ---")
for line in lines[-100:]:
    print(line.strip())
