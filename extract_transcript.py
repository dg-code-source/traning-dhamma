import os
import re
import sys
import json
import argparse
import urllib.request
import urllib.parse
from youtube_transcript_api import YouTubeTranscriptApi


def extract_video_id(url_or_id: str) -> str:
    """Extract YouTube 11-character video ID from various URL formats or raw ID."""
    url_or_id = url_or_id.strip()
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:shorts\/)([0-9A-Za-z_-]{11})',
        r'(?:live\/)([0-9A-Za-z_-]{11})',
        r'^([0-9A-Za-z_-]{11})$'
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    raise ValueError(f"Could not extract a valid YouTube video ID from: '{url_or_id}'")


def get_video_title(video_id: str) -> str:
    """Fetch video title using YouTube oEmbed (no API key required)."""
    oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
    try:
        req = urllib.request.Request(
            oembed_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            title = data.get("title", video_id)
            return title
    except Exception as e:
        print(f"[Warning] Could not fetch video title via oEmbed: {e}. Using video ID as title.")
        return video_id


def sanitize_filename(name: str) -> str:
    """Sanitize string to be a safe filesystem filename."""
    clean = re.sub(r'[\\/*?:"<>|]', '', name)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean if clean else "transcript"


def fetch_transcript(video_id: str, languages=('en', 'en-US', 'en-GB')) -> str:
    """Fetch and format transcript from YouTube."""
    api = YouTubeTranscriptApi()
    try:
        transcript_obj = api.fetch(video_id, languages=languages)
    except Exception:
        try:
            transcript_list = api.list(video_id)
            try:
                transcript_obj = transcript_list.find_transcript(list(languages))
            except Exception:
                # Find any available transcript
                transcript_obj = next(iter(transcript_list))
            transcript_obj = transcript_obj.fetch()
        except Exception as e:
            raise RuntimeError(f"Could not retrieve transcript for video {video_id}: {e}")

    # Merge snippets into clean continuous text paragraphs
    text_chunks = []
    current_chunk = []
    word_count = 0

    for item in transcript_obj:
        text = getattr(item, 'text', None) or (item['text'] if isinstance(item, dict) else str(item))
        text = text.strip()
        if not text or text.lower() in ("[music]", "[applause]"):
            continue
        text = text.replace('\n', ' ')
        current_chunk.append(text)
        word_count += len(text.split())

        # Create paragraph break roughly every 120-180 words after sentence end
        if word_count >= 120 and text.endswith(('.', '?', '!')):
            text_chunks.append(" ".join(current_chunk))
            current_chunk = []
            word_count = 0

    if current_chunk:
        text_chunks.append(" ".join(current_chunk))

    return "\n\n".join(text_chunks)


def main():
    parser = argparse.ArgumentParser(description="Extract clean Dhamma talk transcript from YouTube URL.")
    parser.add_argument("url", help="YouTube video URL or Video ID")
    parser.add_argument("--output_dir", "-o", default=None, help="Directory to save the transcript")
    parser.add_argument("--custom_title", "-t", default=None, help="Custom title for the transcript file")
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    transcripts_dir = args.output_dir or os.path.join(script_dir, "transcripts")
    os.makedirs(transcripts_dir, exist_ok=True)

    print(f"[1/3] Extracting video ID from '{args.url}'...")
    video_id = extract_video_id(args.url)
    print(f"      Video ID: {video_id}")

    print(f"[2/3] Fetching video metadata and title...")
    raw_title = args.custom_title or get_video_title(video_id)
    safe_title = sanitize_filename(raw_title)
    print(f"      Video Title: {safe_title}")

    print(f"[3/3] Downloading and cleaning transcript...")
    transcript_text = fetch_transcript(video_id)

    output_filename = f"{safe_title}.txt"
    output_path = os.path.join(transcripts_dir, output_filename)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(transcript_text)

    print(f"\n[Success] Transcript saved successfully to:")
    print(f"          {output_path}")
    print(f"          Total words: {len(transcript_text.split()):,}")
    print(f"\n[Next Step] Generate QA dataset in datasets/ using Antigravity.")


if __name__ == "__main__":
    main()
