from youtube_transcript_api import YouTubeTranscriptApi
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

v_id = "U03YoHWfJi8"
try:
    ytt = YouTubeTranscriptApi()
    t = ytt.fetch(v_id)
    text = " ".join([entry.text for entry in t])
    print(f"SUCCESS! Fetched {len(text.split())} words for {v_id}")
    print(f"Preview: {text[:200]}...")
except Exception as e:
    err_first = str(e).splitlines()[0] if str(e) else ""
    print(f"Status: {type(e).__name__} -> {err_first}")
