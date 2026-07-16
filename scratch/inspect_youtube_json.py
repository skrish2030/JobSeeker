import requests
import re
import urllib.parse
import json

def inspect():
    query = "tech jobs hiring trends"
    encoded_query = urllib.parse.quote(query)
    url = f"https://www.youtube.com/results?search_query={encoded_query}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    res = requests.get(url, headers=headers, timeout=10)
    match = re.search(r'var ytInitialData\s*=\s*({.*?});', res.text)
    if not match:
        # Try finding with just var ytInitialData = { ... } (without semicolon)
        match = re.search(r'var ytInitialData\s*=\s*({.*?})</script>', res.text)
        
    if not match:
        print("[-] Could not find ytInitialData match!")
        return
        
    data = json.loads(match.group(1))
    print("[+] Successfully parsed ytInitialData JSON.")
    
    # Let's inspect the keys inside data
    print(f"Top-level keys: {list(data.keys())}")
    
    contents = data.get("contents", {})
    print(f"contents keys: {list(contents.keys())}")
    
    # If twoColumnSearchResultRenderer is not present, check what is there
    for k, v in contents.items():
        print(f"  key: {k}")
        if isinstance(v, dict):
            print(f"  value keys: {list(v.keys())}")
            
    # Save a clean snippet to inspect
    with open("scratch/yt_structure.json", "w", encoding="utf-8") as f:
        json.dump(contents, f, indent=2)
    print("[+] Saved scratch/yt_structure.json")

if __name__ == "__main__":
    inspect()
