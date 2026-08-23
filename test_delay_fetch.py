import urllib.request, json, time, sys
from youtube_transcript_api import YouTubeTranscriptApi

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

with open("AjhanSumedho/playlist_manifest.json", "r", encoding="utf-8") as f:
    videos = json.load(f)

pending_vids = [v for v in videos if v.get("status") != "COMPLETED"]
print(f"Total pending/unextracted videos: {len(pending_vids)}")

# Test with standard user agent and cookies fallback
ytt = YouTubeTranscriptApi()
for v in pending_vids[:5]:
    vid = v["video_id"]
    try:
        t = ytt.fetch(vid)
        text = " ".join([entry.text for entry in t])
        print(f"[SUCCESS] {vid}: {len(text.split())} words")
    except Exception as e:
        print(f"[FAILED] {vid}: {str(e).splitlines()[0] if str(e) else 'Error'}")
    time.sleep(1)
