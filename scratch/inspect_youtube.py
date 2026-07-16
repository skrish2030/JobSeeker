import requests
import re
import urllib.parse

def inspect():
    query = "tech jobs hiring trends"
    encoded_query = urllib.parse.quote(query)
    url = f"https://www.youtube.com/results?search_query={encoded_query}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5"
    }
    
    print(f"[*] Requesting YouTube: {url}")
    try:
        res = requests.get(url, headers=headers, timeout=10)
        print(f"[+] Status Code: {res.status_code}")
        print(f"[+] Final URL after redirects: {res.url}")
        
        # Check if consent page
        if "consent.youtube" in res.url or "consent.google" in res.url:
            print("[!] Redirected to Google Consent page!")
            return
            
        print(f"[+] Response Length: {len(res.text)} characters")
        
        # Look for script patterns containing ytInitialData
        matches = re.findall(r'ytInitialData', res.text)
        print(f"[+] Occurrences of 'ytInitialData': {len(matches)}")
        
        # Find where it is
        for m in re.finditer(r'ytInitialData', res.text):
            start = max(0, m.start() - 50)
            end = min(len(res.text), m.end() + 200)
            print(f"  Snippet: {res.text[start:end]}")
            
    except Exception as e:
        print(f"[-] Error: {e}")

if __name__ == "__main__":
    inspect()
