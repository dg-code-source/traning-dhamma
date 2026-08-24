import os, sys, json, tempfile
import yt_dlp

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def get_transcript_via_ytdlp_native(video_id: str) -> str:
    url = f"https://www.youtube.com/watch?v={video_id}"
    with tempfile.TemporaryDirectory() as tmpdir:
        out_tmpl = os.path.join(tmpdir, "%(id)s.%(ext)s")
        ydl_opts = {
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['en', 'en-.*'],
            'subtitlesformat': 'vtt/srv1/ttml/best',
            'outtmpl': out_tmpl,
            'quiet': True,
            'no_warnings': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'ios']
                }
            }
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        files = os.listdir(tmpdir)
        print(f"Downloaded files in tmpdir: {files}")
        for f in files:
            if f.endswith(('.vtt', '.ttml', '.srv1', '.sub', '.srt')):
                with open(os.path.join(tmpdir, f), 'r', encoding='utf-8', errors='ignore') as sfile:
                    content = sfile.read()
                    # Clean VTT timestamps
                    import re
                    clean_lines = []
                    for line in content.splitlines():
                        if '-->' in line or line.startswith('WEBVTT') or line.startswith('Kind:') or line.startswith('Language:'):
                            continue
                        # Remove html tags
                        c_line = re.sub(r'<[^>]+>', '', line).strip()
                        if c_line and not c_line.isdigit() and (not clean_lines or clean_lines[-1] != c_line):
                            clean_lines.append(c_line)
                    return " ".join(clean_lines)
    return ""

v_id = "U03YoHWfJi8"
print(f"Testing native yt-dlp downloader on {v_id} ...")
txt = get_transcript_via_ytdlp_native(v_id)
print(f"Success! Extracted {len(txt.split())} words.")
print(f"Preview: {txt[:300]}...")
