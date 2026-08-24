import sys, json, time
from youtube_transcript_api import YouTubeTranscriptApi

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

with open("AjhanSumedho/playlist_manifest.json", "r", encoding="utf-8") as f:
    videos = json.load(f)

pending_vids = [v for v in videos if v.get("status") != "COMPLETED"]
print(f"Testing {len(pending_vids)} pending videos...")

ytt = YouTubeTranscriptApi()
for v in pending_vids[:5]:
    vid = v["video_id"]
    title = v.get("title", "")[:45]
    try:
        t = ytt.fetch(vid)
        text = " ".join([entry.text for entry in t])
        print(f"  [SUCCESS] {vid} ({title}): {len(text.split())} words")
    except Exception as e:
        first_line = str(e).splitlines()[0] if str(e).strip() else "Error"
        print(f"  [FAILED] {vid}: {first_line}")
    time.sleep(1)
