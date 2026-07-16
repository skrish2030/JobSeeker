import re

log_path = r"C:\Users\skris\.gemini\antigravity\brain\343b1e07-cd94-460b-aa2c-ed1275c0e158\.system_generated\tasks\task-3621.log"

with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

print(f"Total log lines: {len(lines)}")
print("--- Non-metrics or error/warning log lines ---")
count = 0
for line in lines:
    if "GET /metrics" in line:
        continue
    # print any warnings, errors, or requests
    if "ERROR" in line or "WARNING" in line or "INFO:" in line or "Traceback" in line or "Exception" in line:
        print(line.strip())
        count += 1
        if count > 100:
            print("... truncated after 100 lines ...")
            break
