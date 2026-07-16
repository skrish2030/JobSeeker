with open("frontend/app.js", "r", encoding="utf-8") as file:
    content = file.readlines()

start = 790
end = 830
print(f"--- app.js lines {start+1} to {end} ---")
for idx in range(start, end):
    print(f"{idx+1}: {content[idx].strip()}")
