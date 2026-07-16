log_path = r"C:\Users\skris\.gemini\antigravity\brain\343b1e07-cd94-460b-aa2c-ed1275c0e158\.system_generated\tasks\task-4058.log"

with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

print("--- Remote Browser Console Logs ---")
count = 0
for line in lines:
    if "[BROWSER CONSOLE" in line or "[DEBUG]" in line:
        print(line.strip())
        count += 1

if count == 0:
    print("No remote console logs found yet.")
