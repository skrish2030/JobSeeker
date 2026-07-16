import os

log_path = r"c:\Users\skris\OneDrive\Desktop\JobSeeker\.monitoring\grafana-v10.4.2\data\log\grafana.log"
if os.path.exists(log_path):
    with open(log_path, "r", encoding="utf-8", errors="ignore") as file:
        lines = file.readlines()
    print(f"Total lines: {len(lines)}")
    print("Last 80 lines:")
    for line in lines[-80:]:
        print(line.strip())
else:
    print(f"Log file not found: {log_path}")
