import urllib.request, re, json, sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

v_id = "U03YoHWfJi8"
url = f"https://www.youtube.com/watch?v={v_id}"

h = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"}
req = urllib.request.Request(url, headers=h)
html = urllib.request.urlopen(req).read().decode("utf-8")

# Extract captionTracks using regex to avoid json parsing glitches
urls = re.findall(r'"baseUrl":"(https:[^"]*timedtext[^"]*)"', html)
print(f"Found {len(urls)} timedtext URLs in Desktop response:")
for u in urls[:2]:
    clean_u = u.replace(r"\u0026", "&")
    print(f"  Attempting fetch on: {clean_u[:80]}...")
    try:
        cap_req = urllib.request.Request(clean_u, headers=h)
        cap_data = urllib.request.urlopen(cap_req).read().decode('utf-8')
        print(f"  [SUCCESS] Downloaded {len(cap_data)} bytes of captions!")
        # Extract text
        text_content = " ".join(re.findall(r'<text[^>]*>(.*?)</text>', cap_data))
        print(f"  Word count: {len(text_content.split())}")
        print(f"  Preview: {text_content[:200]}...")
        break
    except Exception as e:
        print(f"  Fetch failed: {e}")
