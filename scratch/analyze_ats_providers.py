import json

with open("us_companies_job_portals.json", "r", encoding="utf-8") as file:
    portals = json.load(file)

greenhouse_count = 0
lever_count = 0
other_count = 0

for p in portals:
    url = p.get("career_portal_url", "")
    if "greenhouse" in url:
        greenhouse_count += 1
    elif "lever.co" in url:
        lever_count += 1
    else:
        other_count += 1

print(f"Total portals: {len(portals)}")
print(f"Greenhouse portals: {greenhouse_count}")
print(f"Lever portals: {lever_count}")
print(f"Other portals: {other_count}")
