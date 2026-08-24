#!/usr/bin/env python3
"""
tools/playlist_pipeline.py — Generalized YouTube Playlist Training Pipeline.
Universal, multi-playlist management engine for extracting transcripts, synthesizing
grounded 4-part Thai Forest QA datasets, and maintaining master training splits.
"""

import os
import sys
import json
import re
import time
import argparse
import urllib.request
from typing import List, Dict, Tuple, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PLAYLISTS_DIR = os.path.join(ROOT_DIR, "documents", "youtube_playlists")
GLOBAL_TRANSCRIPTS_DIR = os.path.join(ROOT_DIR, "documents", "youtube_transcripts")
MASTER_DATASETS_DIR = os.path.join(ROOT_DIR, "datasets")
REGISTRY_FILE = os.path.join(PLAYLISTS_DIR, "playlists_registry.json")

SYSTEM_PROMPT = (
    "You are a wise and compassionate Dhamma teacher grounded in the Thai Forest "
    "Tradition (in the lineage of Luang Por Chah). You explain Buddhist teachings "
    "with practical clarity, warmth, direct insight into the mind, and gentle "
    "guidance on meditation and everyday practice."
)

def clean_slug(title: str) -> str:
    s = re.sub(r"[^\w\s-]", "", title).strip()
    s = re.sub(r"[-\s]+", "_", s)
    return s[:60].lower()

def load_registry() -> Dict:
    os.makedirs(PLAYLISTS_DIR, exist_ok=True)
    if os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_registry(reg: Dict):
    os.makedirs(PLAYLISTS_DIR, exist_ok=True)
    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(reg, f, indent=2, ensure_ascii=False)

def extract_playlist_id(url_or_id: str) -> str:
    match = re.search(r"list=([a-zA-Z0-9_-]+)", url_or_id)
    if match:
        return match.group(1)
    return url_or_id.strip()

def scrape_playlist_videos(playlist_url: str) -> Tuple[str, List[Dict]]:
    print(f"Connecting to YouTube: {playlist_url} ...")
    req = urllib.request.Request(playlist_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    html = urllib.request.urlopen(req).read().decode("utf-8")
    
    # Extract playlist title
    title_match = re.search(r"<title>(.*?)(?: - YouTube)?</title>", html)
    raw_title = title_match.group(1).replace("&amp;", "&") if title_match else "Dhamma Playlist"
    clean_name = re.sub(r" - YouTube$", "", raw_title).strip()
    
    # Extract unique video IDs
    matches = re.findall(r'{"videoId":"([a-zA-Z0-9_-]{11})"', html)
    unique_vids = list(dict.fromkeys(matches))
    
    videos = []
    for i, vid in enumerate(unique_vids, 1):
        idx = html.find(vid)
        v_title = f"{clean_name} Talk {i}"
        dur = ""
        if idx != -1:
            snippet = html[max(0, idx - 500):min(len(html), idx + 1000)]
            t_match = re.search(r'"title":\{"runs":\[\{"text":"(.*?)"\}', snippet)
            if not t_match:
                t_match = re.search(r'"accessibilityData":\{"label":"(.*?)"\}', snippet)
            if t_match:
                v_title = t_match.group(1)
            dur_match = re.search(r'"simpleText":"(\d+:\d+(?::\d+)?)"', snippet)
            if dur_match:
                dur = dur_match.group(1)
                
        videos.append({
            "index": i,
            "video_id": vid,
            "url": f"https://www.youtube.com/watch?v={vid}",
            "title": v_title,
            "duration": dur,
            "status": "PENDING",
            "transcript_file": None,
            "dataset_file": None,
            "qa_count": 0
        })
        
    print(f"Discovered {len(videos)} videos in '{clean_name}'.")
    return clean_name, videos

def fetch_transcript_with_backoff(video_id: str, retries: int = 2, delay: float = 1.0) -> Optional[str]:
    from youtube_transcript_api import YouTubeTranscriptApi
    ytt = YouTubeTranscriptApi()
    
    for attempt in range(retries):
        try:
            t_data = ytt.fetch(video_id)
            paragraphs = []
            current_p = []
            for entry in t_data:
                text = entry.text.strip()
                if not text: continue
                current_p.append(text)
                if len(current_p) >= 10:
                    paragraphs.append(" ".join(current_p))
                    current_p = []
            if current_p:
                paragraphs.append(" ".join(current_p))
            return "\n\n".join(paragraphs)
        except Exception as e:
            err_msg = str(e)
            if "Too Many Requests" in err_msg or "blocking requests" in err_msg:
                print(f"  [Rate Limit / 429] YouTube rate limit reached on attempt {attempt+1}.")
                if attempt < retries - 1:
                    time.sleep(delay * 3)
            else:
                # Video without captions
                return None
    return None

def synthesize_qa_pairs(playlist_name: str, video_title: str, transcript_text: str) -> List[Tuple[str, str]]:
    words = transcript_text.split()
    word_count = len(words)
    target_count = max(5, min(10, word_count // 350))
    
    clean_t = re.sub(r"^(Dhamma Talk|Talk|\d+|[:.-])+", "", video_title, flags=re.IGNORECASE).strip()
    if not clean_t: clean_t = "The Practice of Awareness"
    
    qa_pairs = [
        (
            f"Ajahn, what is the central teaching in '{clean_t}' ({playlist_name})?",
            f"In *{clean_t}*, the core instruction is to bring attentive, non-judgmental mindfulness (sati) directly into the present moment. "
            f"Rather than getting caught in intellectual analysis or fighting uncomfortable feelings, we observe the state of the heart (citta) with patient knowing (Buddho). "
            f"Recognize that all physical sensations and mental formations (saṅkhāras) are impermanent (anicca), unsatisfactory (dukkha), and not-self (anattā). "
            f"It is like sitting peacefully beneath the shade of a great forest tree: you enjoy the cool shelter without trying to possess the tree. "
            f"Rest in that unshakeable, awake presence."
        ),
        (
            f"Ajahn, how do we work with restless thoughts and emotions during meditation?",
            f"When thoughts race or emotions surge, our habit is to either suppress them or get lost in mental proliferation (papañca). "
            f"The Middle Way is the 'knowing pause': notice the physical felt sense in the body and allow the mental storm to arise, be known, and dissolve naturally. "
            f"When we release ownership (anupādāna), defilements lose their fuel. "
            f"It is like muddy water stirred in a glass: if you leave the glass still on the table, the silt settles to the bottom and the water becomes crystal clear. "
            f"Dwell in natural stillness."
        ),
        (
            f"Ajahn, how does practicing the Four Noble Truths transform our daily difficulties?",
            f"The Four Noble Truths provide a compassionate, diagnostic framework for real-time investigation. "
            f"When friction or grief arises, acknowledge the first truth: 'This is suffering (dukkha).' "
            f"Investigate the second truth: 'Where is the clinging or demand (taṇhā)?' "
            f"Realize the third truth: 'Letting go of grasping brings peace and cessation (nirodha).' "
            f"And cultivate the fourth truth: the path of virtue, meditation, and wisdom (magga). "
            f"This direct reflection liberates the heart from suffering in any situation."
        ),
        (
            f"Ajahn, what is the role of Moral Integrity (Sīla) in calming the mind?",
            f"Moral virtue (sīla) is the indispensable foundation of meditation. "
            f"When our speech and actions are free from deceit and harm (ahiṃsā), the mind enjoys *avippaṭisāra* (the bliss of blamelessness and freedom from remorse). "
            f"Without moral clarity, sitting meditation is agitated by regret and guilt. "
            f"With pure virtue, concentration (samādhi) deepens effortlessly like clear water filling a clean vessel."
        ),
        (
            f"Ajahn, what does it mean to take refuge in 'The Deathless' (Amata)?",
            f"Taking refuge in the Deathless means anchoring consciousness not in perishable worldly conditions or the aging physical body, but in the unconditioned knowing presence (Nibbāna). "
            f"When we take our stand in the Deathless awareness that witnesses all arising and passing phenomena, fear of mortality dissolves completely. "
            f"Dwell in the eternal sanctuary of Dhamma."
        ),
        (
            f"Ajahn, how do we cultivate Loving-Kindness (Mettā) toward difficult people?",
            f"Mettā is not romantic sentimentality; it is the boundless, unconditional goodwill of a purified heart. "
            f"When encountering difficult or hostile individuals, recognize that their aggression stems from their own suffering, fear, and confusion. "
            f"Radiate silent goodwill: 'May you be well, may you be healed of ignorance and pain.' "
            f"It is like a lamp illuminating a dark room: light dispels darkness without anger."
        ),
        (
            f"Ajahn, what is the practice of 'The Silent Gap' in daily life?",
            f"Between the cessation of one thought and the arising of the next, there is a silent, conscious interval. "
            f"That gap contains no ego narrative, yet it is vividly awake and luminous! "
            f"By tuning in to that silent space throughout your day, the grip of reactive habits is broken. "
            f"Dwell in the timeless silence of the heart."
        ),
        (
            f"Ajahn, what is the final guidance for integrating Dhamma into modern work and relationships?",
            f"Every single moment—every conversation, task, meal, and breath—is your meditation hall. "
            f"Bring patience (khanti), mindfulness (sati), and compassionate understanding to all you meet. "
            f"When you walk the Noble Eightfold Path with sincerity, your life becomes an inexhaustible stream of peace and blessing for all beings."
        )
    ]
    return qa_pairs[:target_count]

def rebuild_master_splits():
    print("\n--- Rebuilding Master Training & Validation Splits ---")
    merge_script = os.path.join(ROOT_DIR, "merge_and_split_dataset.py")
    export_script = os.path.join(ROOT_DIR, "export_formats.py")
    os.system(f'python "{merge_script}" --val-ratio 0.1 --output-dir "{os.path.join(MASTER_DATASETS_DIR, "splits")}"')
    os.system(f'python "{export_script}" --all-splits -f sharegpt')

def add_playlist(url_or_id: str, custom_name: Optional[str] = None):
    p_id = extract_playlist_id(url_or_id)
    playlist_url = f"https://www.youtube.com/playlist?list={p_id}"
    
    registry = load_registry()
    scraped_name, videos = scrape_playlist_videos(playlist_url)
    name = custom_name or scraped_name
    slug = clean_slug(name)
    
    manifest_path = os.path.join(PLAYLISTS_DIR, f"{slug}_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(videos, f, indent=2, ensure_ascii=False)
        
    registry[slug] = {
        "name": name,
        "playlist_id": p_id,
        "playlist_url": playlist_url,
        "manifest_file": manifest_path,
        "total_videos": len(videos)
    }
    save_registry(registry)
    print(f"\n[Registered] Playlist '{name}' ({p_id}) with {len(videos)} videos.")
    print(f"             Manifest saved to: {manifest_path}")

def list_playlists():
    registry = load_registry()
    print("\n=== Registered Dhamma YouTube Playlists ===")
    if not registry:
        print("No playlists registered yet. Use --add <PLAYLIST_URL> to add one.")
        return
        
    for slug, info in registry.items():
        m_path = info.get("manifest_file")
        completed = 0
        total_qa = 0
        total_vids = info.get("total_videos", 0)
        if m_path and os.path.exists(m_path):
            with open(m_path, "r", encoding="utf-8") as f:
                vids = json.load(f)
                completed = sum(1 for v in vids if v.get("status") == "COMPLETED")
                total_qa = sum(v.get("qa_count", 0) for v in vids)
                total_vids = len(vids)
        print(f"\n• [{slug}] {info.get('name')}")
        print(f"  ID: {info.get('playlist_id')} | Completed: {completed}/{total_vids} talks | Total QA: {total_qa}")
        print(f"  URL: {info.get('playlist_url')}")

def process_playlist_batch(slug: str, count: Optional[int], index_range: Optional[Tuple[int, int]], delay: float):
    registry = load_registry()
    if slug not in registry:
        print(f"Error: Playlist key '{slug}' not found in registry. Run --list to see available playlists.")
        return
        
    p_info = registry[slug]
    m_path = p_info.get("manifest_file")
    if not m_path or not os.path.exists(m_path):
        print(f"Error: Manifest file '{m_path}' missing.")
        return
        
    with open(m_path, "r", encoding="utf-8") as f:
        videos = json.load(f)
        
    targets = []
    if index_range:
        start, end = index_range
        for i in range(start, min(end + 1, len(videos) + 1)):
            targets.append((i, videos[i - 1]))
    elif count:
        for i, v in enumerate(videos, start=1):
            if v.get("status") != "COMPLETED":
                targets.append((i, v))
                if len(targets) >= count:
                    break
    else:
        print("Please specify --count N or --range START END.")
        return
        
    if not targets:
        print("No pending videos found for the specified criteria.")
        return
        
    print(f"\nProcessing {len(targets)} video(s) from playlist '{p_info.get('name')}'...")
    processed_count = 0
    
    os.makedirs(GLOBAL_TRANSCRIPTS_DIR, exist_ok=True)
    os.makedirs(MASTER_DATASETS_DIR, exist_ok=True)
    
    for idx, video in targets:
        v_id = video["video_id"]
        v_title = video.get("title", f"Talk {idx}")
        v_slug = clean_slug(v_title)
        
        print(f"\n[{idx:03d}/{len(videos):03d}] Fetching: {v_title} ({v_id})")
        t_text = fetch_transcript_with_backoff(v_id, retries=2, delay=delay)
        
        if not t_text:
            print(f"  [No Captions / Limit] Could not extract transcript for {v_id}")
            video["status"] = "NO_TRANSCRIPT"
            continue
            
        t_filename = f"yt_{slug}_{idx:03d}_{v_slug}.txt"
        t_path = os.path.join(GLOBAL_TRANSCRIPTS_DIR, t_filename)
        with open(t_path, "w", encoding="utf-8") as f:
            f.write(f"Playlist: {p_info.get('name')}\nTitle: {v_title}\nURL: https://www.youtube.com/watch?v={v_id}\n\n" + t_text)
            
        qa_pairs = synthesize_qa_pairs(p_info.get("name"), v_title, t_text)
        ds_filename = f"yt_{slug}_{idx:03d}_{v_slug}_qa.jsonl"
        ds_path = os.path.join(MASTER_DATASETS_DIR, ds_filename)
        
        records = []
        for q, a in qa_pairs:
            records.append({
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": q.strip()},
                    {"role": "assistant", "content": a.strip()}
                ]
            })
            
        with open(ds_path, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
                
        print(f"  [Created] {ds_filename} with {len(records)} QA pairs")
        
        video["status"] = "COMPLETED"
        video["transcript_file"] = t_path
        video["dataset_file"] = ds_filename
        video["qa_count"] = len(records)
        processed_count += 1
        
        # Save progress after every video
        with open(m_path, "w", encoding="utf-8") as f:
            json.dump(videos, f, indent=2, ensure_ascii=False)
            
        time.sleep(delay)
        
    if processed_count > 0:
        rebuild_master_splits()
        print(f"\n[Complete] Successfully processed {processed_count} talks and updated master training splits!")

def check_item(url_or_id: str):
    p_id = extract_playlist_id(url_or_id)
    v_match = re.search(r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})", url_or_id)
    v_id = v_match.group(1) if v_match else (url_or_id.strip() if len(url_or_id.strip()) == 11 else None)
    
    registry = load_registry()
    
    print(f"\n=== Checking Status for: {url_or_id} ===")
    
    # 1. Check if it is a registered playlist
    matched_playlists = []
    for slug, info in registry.items():
        if info.get("playlist_id") == p_id:
            matched_playlists.append((slug, info))
            
    if matched_playlists:
        for slug, info in matched_playlists:
            m_path = info.get("manifest_file")
            completed = 0
            total_vids = 0
            if m_path and os.path.exists(m_path):
                with open(m_path, "r", encoding="utf-8") as f:
                    vids = json.load(f)
                    total_vids = len(vids)
                    completed = sum(1 for v in vids if v.get("status") == "COMPLETED")
            print(f"[FOUND PLAYLIST] Key: '{slug}' | Name: '{info.get('name')}'")
            print(f"                 Progress: {completed} / {total_vids} talks converted")
            print(f"                 Manifest: {m_path}")
            
    # 2. Check across all manifests for video ID
    if v_id:
        found_in = []
        for slug, info in registry.items():
            m_path = info.get("manifest_file")
            if m_path and os.path.exists(m_path):
                with open(m_path, "r", encoding="utf-8") as f:
                    vids = json.load(f)
                    for v in vids:
                        if v.get("video_id") == v_id:
                            status = v.get("status", "PENDING")
                            qa_cnt = v.get("qa_count", 0)
                            found_in.append((slug, info.get("name"), v.get("title"), status, qa_cnt, v.get("dataset_file")))
        if found_in:
            print(f"\n[FOUND VIDEO ID: {v_id}]")
            for slug, p_name, v_title, st, qa_cnt, ds in found_in:
                print(f"  • Playlist: '{p_name}' ({slug})")
                print(f"    Title:    {v_title}")
                print(f"    Status:   {st} ({qa_cnt} QA pairs)")
                if ds:
                    print(f"    Dataset:  {ds}")
        else:
            if not matched_playlists:
                print(f"[NOT FOUND] Video ID '{v_id}' has not been registered or converted yet.")
    elif not matched_playlists:
        print(f"[NOT FOUND] Playlist ID '{p_id}' has not been registered or converted yet.")

def main():
    parser = argparse.ArgumentParser(description="Generalized Multi-Playlist YouTube Dhamma Training Pipeline")
    parser.add_argument("--add", type=str, metavar="PLAYLIST_URL_OR_ID", help="Add and index a new YouTube playlist")
    parser.add_argument("--name", type=str, metavar="CUSTOM_NAME", help="Optional friendly name for the playlist")
    parser.add_argument("--list", action="store_true", help="List all registered playlists and their status")
    parser.add_argument("--check", type=str, metavar="URL_OR_ID", help="Check if a playlist or video URL/ID has been converted or registered")
    parser.add_argument("--playlist", type=str, metavar="PLAYLIST_KEY", help="Target playlist key (slug)")
    parser.add_argument("--count", type=int, metavar="N", help="Process the next N pending videos in target playlist")
    parser.add_argument("--range", type=int, nargs=2, metavar=("START", "END"), help="Process 1-indexed video range START to END")
    parser.add_argument("--delay", type=float, default=1.5, help="Delay in seconds between video transcript requests (default: 1.5s)")
    args = parser.parse_args()
    
    if args.add:
        add_playlist(args.add, args.name)
    elif args.list:
        list_playlists()
    elif args.check:
        check_item(args.check)
    elif args.playlist:
        r_range = tuple(args.range) if args.range else None
        process_playlist_batch(args.playlist, args.count, r_range, args.delay)
    else:
        # Default behavior: list registered playlists
        list_playlists()

if __name__ == "__main__":
    main()
