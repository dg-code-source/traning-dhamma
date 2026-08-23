import urllib.request, re, json, sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

playlist_url = "https://www.youtube.com/playlist?list=PL--llepYBCu4lh112KIeRZ75keS_283ox"
req = urllib.request.Request(playlist_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
html = urllib.request.urlopen(req).read().decode("utf-8")

# Let's find videoId occurrences with surrounding context
pattern = r'{"videoId":"([a-zA-Z0-9_-]{11})"(.*?)}'
matches = re.findall(r'{"videoId":"([a-zA-Z0-9_-]{11})"', html)
unique_vids = list(dict.fromkeys(matches))
print(f"Total Unique Video IDs extracted: {len(unique_vids)}")

# Let's extract titles by finding where each videoId appears with text
videos = []
for i, vid in enumerate(unique_vids, 1):
    # Search for title near this video ID
    idx = html.find(vid)
    title = f"Ajahn Sumedho Dhamma Talk {i}"
    dur = ""
    if idx != -1:
        snippet = html[max(0, idx - 500):min(len(html), idx + 1000)]
        # Try to find title
        t_match = re.search(r'"title":\{"runs":\[\{"text":"(.*?)"\}', snippet)
        if not t_match:
            t_match = re.search(r'"accessibilityData":\{"label":"(.*?)"\}', snippet)
        if t_match:
            title = t_match.group(1)
        dur_match = re.search(r'"simpleText":"(\d+:\d+(?::\d+)?)"', snippet)
        if dur_match:
            dur = dur_match.group(1)
            
    videos.append({
        "index": i,
        "video_id": vid,
        "url": f"https://www.youtube.com/watch?v={vid}",
        "title": title,
        "duration": dur
    })

print(f"Successfully processed {len(videos)} video URLs:")
for v in videos[:10]:
    print(f"  [{v['index']:03d}] {v['title'][:60]} | {v['duration']} | {v['url']}")
