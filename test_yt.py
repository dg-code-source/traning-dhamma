import urllib.request, re, json, sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

playlist_url = 'https://www.youtube.com/playlist?list=PL--llepYBCu4lh112KIeRZ75keS_283ox'
req = urllib.request.Request(playlist_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
html = urllib.request.urlopen(req).read().decode('utf-8')
video_ids = list(dict.fromkeys(re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)))
# Title extraction
title_match = re.search(r'<title>(.*?)</title>', html)
title = title_match.group(1) if title_match else 'Unknown'
print(f"Playlist Page Title: {title}")
print(f"Total Video IDs Found in initial load: {len(video_ids)}")
print("First 10 IDs:", video_ids[:10])
