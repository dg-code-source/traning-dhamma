import urllib.request, re, json, sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

vid = "U03YoHWfJi8"
url = f"https://www.youtube.com/watch?v={vid}"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
html = urllib.request.urlopen(req).read().decode("utf-8")

# Look for captionTracks in html
match = re.search(r'"captionTracks":\[(.*?)\]', html)
if match:
    print(f"Found captionTracks for {vid} directly in HTML!")
    raw = f"[{match.group(1)}]"
    tracks = json.loads(raw)
    for t in tracks:
        print(f"  Language: {t.get('name', {}).get('simpleText', '')} ({t.get('languageCode')}) -> BaseURL: {t.get('baseUrl')[:60]}...")
        # Fetch caption XML
        cap_url = t.get('baseUrl')
        if cap_url:
            cap_req = urllib.request.Request(cap_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            cap_xml = urllib.request.urlopen(cap_req).read().decode('utf-8')
            clean_text = " ".join(re.findall(r'<text[^>]*>(.*?)</text>', cap_xml))
            print(f"  Extracted text length: {len(clean_text.split())} words")
            print(f"  Preview: {clean_text[:150]}...")
else:
    print(f"No captionTracks in HTML for {vid}.")
