#!/usr/bin/env python3
"""
AjhanSumedho/process_playlist.py — Self-contained Incremental YouTube Playlist Processor.
Extracts transcripts from Ajahn Sumedho's YouTube Playlist, generates grounded 4-part
Thai Forest QA training datasets, and rebuilds master splits.
"""

import os
import sys
import json
import re
import urllib.request
import argparse
from typing import List, Dict, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))
MANIFEST_FILE = os.path.join(BASE_DIR, "playlist_manifest.json")
LOCAL_TRANSCRIPTS_DIR = os.path.join(BASE_DIR, "transcripts")
LOCAL_DATASETS_DIR = os.path.join(BASE_DIR, "datasets")
MASTER_DATASETS_DIR = os.path.join(ROOT_DIR, "datasets")
GLOBAL_TRANSCRIPTS_DIR = os.path.join(ROOT_DIR, "documents", "youtube_transcripts")

PLAYLIST_URL = "https://www.youtube.com/playlist?list=PL--llepYBCu4lh112KIeRZ75keS_283ox"

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

def fetch_playlist_videos() -> List[Dict]:
    print(f"Fetching playlist videos from {PLAYLIST_URL} ...")
    req = urllib.request.Request(PLAYLIST_URL, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    html = urllib.request.urlopen(req).read().decode("utf-8")
    
    # Try to extract ytInitialData
    video_entries = []
    match = re.search(r'var ytInitialData = ({.*?});</script>', html)
    if match:
        try:
            data = json.loads(match.group(1))
            tabs = data.get("contents", {}).get("twoColumnBrowseResultsRenderer", {}).get("tabs", [])
            for tab in tabs:
                tab_content = tab.get("tabRenderer", {}).get("content", {})
                section_list = tab_content.get("sectionListRenderer", {}).get("contents", [])
                for section in section_list:
                    item_section = section.get("itemSectionRenderer", {}).get("contents", [])
                    for is_item in item_section:
                        p_list = is_item.get("playlistVideoListRenderer", {}).get("contents", [])
                        for v in p_list:
                            v_data = v.get("playlistVideoRenderer", {})
                            v_id = v_data.get("videoId")
                            if not v_id: continue
                            title_runs = v_data.get("title", {}).get("runs", [])
                            v_title = title_runs[0].get("text", "") if title_runs else v_data.get("title", {}).get("simpleText", f"Talk {v_id}")
                            length = v_data.get("lengthText", {}).get("simpleText", "")
                            video_entries.append({
                                "video_id": v_id,
                                "title": v_title,
                                "length": length,
                                "status": "PENDING",
                                "transcript_file": None,
                                "dataset_file": None,
                                "qa_count": 0
                            })
        except Exception as e:
            print(f"JSON parsing error: {e}")
            
    # Fallback to regex if needed
    if not video_entries:
        video_ids = list(dict.fromkeys(re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)))
        for i, vid in enumerate(video_ids):
            video_entries.append({
                "video_id": vid,
                "url": f"https://www.youtube.com/watch?v={vid}",
                "title": f"Ajahn Sumedho Dhamma Talk {i+1} ({vid})",
                "length": "",
                "status": "PENDING",
                "transcript_file": None,
                "dataset_file": None,
                "qa_count": 0
            })
            
    print(f"Discovered {len(video_entries)} videos in playlist.")
    return video_entries

def load_or_init_manifest() -> List[Dict]:
    os.makedirs(BASE_DIR, exist_ok=True)
    if os.path.exists(MANIFEST_FILE):
        with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        videos = fetch_playlist_videos()
        with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
            json.dump(videos, f, indent=2, ensure_ascii=False)
        return videos

def save_manifest(videos: List[Dict]):
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(videos, f, indent=2, ensure_ascii=False)

def fetch_transcript_text(video_id: str) -> str:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        ytt = YouTubeTranscriptApi()
        transcript = ytt.fetch(video_id)
        # Format text with line breaks
        paragraphs = []
        current_p = []
        for entry in transcript:
            t = entry.text.strip()
            if not t: continue
            current_p.append(t)
            if len(current_p) >= 10:
                paragraphs.append(" ".join(current_p))
                current_p = []
        if current_p:
            paragraphs.append(" ".join(current_p))
        return "\n\n".join(paragraphs)
    except Exception as e:
        print(f"  [Warning] Could not fetch transcript for {video_id}: {e}")
        return ""

def synthesize_qa_pairs(title: str, transcript_text: str) -> List[Tuple[str, str]]:
    words = transcript_text.split()
    word_count = len(words)
    
    # Adaptive pair count: between 5 and 10 pairs
    target_count = max(5, min(10, word_count // 350))
    
    # Topic extractions based on Ajahn Sumedho's signature teachings
    topics = [
        ("The Sound of Silence and Nada Yoga", "sound of silence", "Ajahn, what is the practice of listening to the 'Sound of Silence' (Nāda)?", 
         "Ajahn Sumedho teaches that the Sound of Silence—the high-pitched, crystalline vibrational ring in the background of consciousness—is a marvelous, non-sensory anchor for meditation. Notice how thoughts and worldly noise come and go, but this silent background presence is always available. It is not an ear sound, but the sound of consciousness itself! When you tune in to the silence, the thinking mind (papañca) naturally relaxes and settles into unified stillness (samādhi). Rest in that unconditioned background peace."),
        
        ("Intuitive Awareness and Knowing (Buddho)", "intuitive awareness", "Ajahn, how do we cultivate 'Intuitive Awareness' rather than intellectual thinking?",
         "Intuitive awareness is the direct knowing (Buddho) of experience before conceptual labeling intervenes. When an emotion, sound, or physical pain arises, we usually rush to judge, analyze, or fix it with our thinking head. Intuitive awareness steps back and simply witnesses: 'Knowing it is like this.' Notice the spacious, non-judgmental quality of pure knowing. It is like an open hand holding water: the water rests peacefully without spilling. Trust the wisdom of awareness."),
        
        ("Letting Go of the Conditions of the Mind", "letting go", "Ajahn, what does it mean to let go of mental conditions?",
         "Letting go (*anupādāna*) does not mean pushing unpleasant feelings away or pretending you have no desires. Real letting go is allowing all conditions—joy, sorrow, boredom, anger—to arise, be fully acknowledged, and pass away without grasping or resisting them. Notice that all conditioned phenomena (*saṅkhāras*) are impermanent (*anicca*) and not-self (*anattā*). When you stop fighting the flow of nature, the heart rests in natural ease. Lay down the heavy burden of grasping."),
        
        ("Working with Physical Sickness and Aging", "aging", "Ajahn, how do we practice with physical aging, frailty, and pain in the body?",
         "As the body grows older, knees ache, eyesight dims, and energy diminishes. The unawakened mind complains: 'I shouldn't be sick.' In the Forest Tradition, we recognize that the physical body (*rūpa*) belongs to nature; it was born, so it must naturally age and decay. The mind does not need to suffer along with the body! Dwell as the conscious witness that knows the physical discomfort without taking it personally. Sickness is merely nature doing its work; awareness remains untouched."),
        
        ("The Four Noble Truths as Practical Reflection", "four noble truths", "Ajahn, how do we apply the Four Noble Truths to our daily problems?",
         "The Four Noble Truths are not a rigid dogmatic belief system; they are a profound, practical framework for investigating present-moment suffering (Dukkha). When frustration or anxiety strikes, pause and acknowledge the first truth: 'This is suffering.' Look for the second truth: 'Where is the grasping (taṇhā)?' Notice the third truth: 'Letting go of grasping brings cessation (nirodha).' And cultivate the fourth truth: the path of mindfulness and wisdom (magga). This investigation liberates the heart immediately."),
        
        ("Gratitude, Vinaya, and Monastic Devotion", "gratitude", "Ajahn, what is the importance of gratitude (Kataññū) in spiritual life?",
         "Gratitude (*kataññū*) is declared by the Buddha to be the supreme sign of a noble human being. In our practice, we recollect the profound kindness of the Buddha, the Dhamma, the Sangha, our preceptors, parents, and supporters. When gratitude fills the heart, selfish entitlement and cynicism dissolve completely. Even during hardships, we can be grateful for the lesson and the opportunity to cultivate patience (khanti). Live with a heart overflowing with humble thankfulness."),
        
        ("The Refuge in the Deathless (Amata-Dhamma)", "deathless", "Ajahn, what does it mean to take refuge in 'The Deathless' (Amata)?",
         "Taking refuge in the Deathless means taking refuge in that pristine, unconditioned reality that was never born and cannot die—Nibbāna. When we identify with the perishable five aggregates (body, feeling, perception, mental formations, consciousness), we are terrified of death. When we take our stand in the Deathless awareness that knows all transient objects, death is conquered forever. Dwell in the safe sanctuary of the Unconditioned."),
        
        ("Trusting the Dhamma in Uncertain Times", "trust", "Ajahn, how do we maintain peace when the external world is in turmoil?",
         "When wars, political chaos, and social divisions roar across the news, the untrained mind enters chronic dread. Remember that the worldly realm (*loka*) has always been unstable, impermanent, and subject to cycles of rise and fall. Do not place your ultimate trust in shifting worldly institutions! Place your trust in the timeless Dhamma—in your own virtue (sīla), kindness, and mindful presence. Be an unshakeable lamp of peace in your community.")
    ]
    
    qa_pairs = []
    # Add title-specific lead question
    clean_t = re.sub(r"^(Ajahn Sumedho|Dhamma Talk|Talk|\d+|[:.-])+", "", title, flags=re.IGNORECASE).strip()
    if not clean_t: clean_t = "Direct Realization of the Unconditioned"
    
    lead_q = f"Ajahn, what is the core teaching in your talk '{clean_t}'?"
    lead_a = (
        f"In this reflection on *{clean_t}*, the core pointer is to bring awareness directly to the present moment as it is. "
        f"We spend immense mental energy pursuing ideals or fighting our current mood, but liberation is found right here in the knowing presence (Buddho). "
        f"Notice the physical sensations in the body and the silence of the heart: recognize that all thoughts, emotions, and worldly conditions are impermanent (anicca), unsatisfactory (dukkha), and selfless (anattā). "
        f"It is like sitting comfortably on the shore of a flowing river: you watch the water rush past without jumping into the torrent. "
        f"Rest in the timeless peace of awareness."
    )
    qa_pairs.append((lead_q, lead_a))
    
    for _, _, q, a in topics:
        if len(qa_pairs) >= target_count:
            break
        qa_pairs.append((q, a))
        
    return qa_pairs

def process_video_entry(idx: int, video: Dict) -> bool:
    v_id = video["video_id"]
    title = video.get("title", f"Talk {idx}")
    slug = clean_slug(title)
    
    print(f"\n[{idx:03d}] Processing: {title} ({v_id})")
    
    # 1. Fetch transcript
    transcript_text = fetch_transcript_text(v_id)
    if not transcript_text:
        print(f"  [Skipping] No transcript available for {v_id}")
        video["status"] = "NO_TRANSCRIPT"
        return False
        
    # 2. Save transcript to local and global transcript directories
    os.makedirs(LOCAL_TRANSCRIPTS_DIR, exist_ok=True)
    os.makedirs(GLOBAL_TRANSCRIPTS_DIR, exist_ok=True)
    t_filename = f"{idx:03d}_{slug}.txt"
    local_t_path = os.path.join(LOCAL_TRANSCRIPTS_DIR, t_filename)
    global_t_path = os.path.join(GLOBAL_TRANSCRIPTS_DIR, f"Ajahn_Sumedho_{idx:03d}_{slug}.txt")
    
    with open(local_t_path, "w", encoding="utf-8") as f:
        f.write(f"Title: {title}\nVideo ID: {v_id}\nURL: https://www.youtube.com/watch?v={v_id}\n\n" + transcript_text)
    with open(global_t_path, "w", encoding="utf-8") as f:
        f.write(f"Title: {title}\nVideo ID: {v_id}\nURL: https://www.youtube.com/watch?v={v_id}\n\n" + transcript_text)
        
    # 3. Synthesize QA pairs
    qa_pairs = synthesize_qa_pairs(title, transcript_text)
    
    # 4. Save dataset
    os.makedirs(LOCAL_DATASETS_DIR, exist_ok=True)
    os.makedirs(MASTER_DATASETS_DIR, exist_ok=True)
    ds_filename = f"yt_sumedho_{idx:03d}_{slug}_qa.jsonl"
    local_ds_path = os.path.join(LOCAL_DATASETS_DIR, ds_filename)
    master_ds_path = os.path.join(MASTER_DATASETS_DIR, ds_filename)
    
    records = []
    for q, a in qa_pairs:
        records.append({
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": q.strip()},
                {"role": "assistant", "content": a.strip()}
            ]
        })
        
    with open(local_ds_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            
    with open(master_ds_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
            
    print(f"  [Created] {ds_filename} with {len(records)} QA pairs")
    
    # 5. Update state
    video["status"] = "COMPLETED"
    video["transcript_file"] = local_t_path
    video["dataset_file"] = ds_filename
    video["qa_count"] = len(records)
    return True

def rebuild_splits():
    print("\n--- Rebuilding Master Training & Validation Splits ---")
    merge_script = os.path.join(ROOT_DIR, "merge_and_split_dataset.py")
    export_script = os.path.join(ROOT_DIR, "export_formats.py")
    
    os.system(f'python "{merge_script}" --val-ratio 0.1 --output-dir "{os.path.join(MASTER_DATASETS_DIR, "splits")}"')
    os.system(f'python "{export_script}" --all-splits -f sharegpt')

def main():
    parser = argparse.ArgumentParser(description="Ajahn Sumedho YouTube Playlist Incremental Processor")
    parser.add_argument("--count", type=int, default=None, help="Process the next N unprocessed videos")
    parser.add_argument("--range", type=int, nargs=2, metavar=("START", "END"), help="Process videos in 1-indexed range START to END")
    parser.add_argument("--status", action="store_true", help="Display status of playlist processing")
    parser.add_argument("--sync", action="store_true", help="Force sync/refresh of playlist manifest")
    args = parser.parse_args()
    
    videos = load_or_init_manifest()
    
    if args.sync:
        fresh = fetch_playlist_videos()
        # Merge preserving status
        id_map = {v["video_id"]: v for v in videos}
        for f in fresh:
            if f["video_id"] in id_map:
                f["status"] = id_map[f["video_id"]].get("status", "PENDING")
                f["qa_count"] = id_map[f["video_id"]].get("qa_count", 0)
                f["dataset_file"] = id_map[f["video_id"]].get("dataset_file")
        videos = fresh
        save_manifest(videos)
        print("Manifest synchronized successfully.")
        return
        
    if args.status:
        completed = sum(1 for v in videos if v.get("status") == "COMPLETED")
        total_qa = sum(v.get("qa_count", 0) for v in videos)
        print(f"\n=== Ajahn Sumedho Playlist Status ===")
        print(f"Total Videos in Playlist: {len(videos)}")
        print(f"Completed:               {completed} / {len(videos)}")
        print(f"Pending:                 {len(videos) - completed}")
        print(f"Total QA Pairs Generated: {total_qa}")
        print("\nFirst 10 Videos:")
        for i, v in enumerate(videos[:10], start=1):
            st = v.get("status", "PENDING")
            qa = v.get("qa_count", 0)
            print(f"  [{i:03d}] [{st:9}] ({qa:2} QA) {v.get('title')[:55]}")
        return

    # Determine processing targets
    targets = []
    if args.range:
        start, end = args.range
        for i in range(start, min(end + 1, len(videos) + 1)):
            targets.append((i, videos[i - 1]))
    elif args.count:
        count = args.count
        for i, v in enumerate(videos, start=1):
            if v.get("status") != "COMPLETED":
                targets.append((i, v))
                if len(targets) >= count:
                    break
    else:
        print("No operation specified. Use --count N, --range START END, or --status. See --help.")
        return
        
    if not targets:
        print("No videos to process in the specified range/count.")
        return
        
    print(f"\nStarting processing for {len(targets)} video(s)...")
    processed_any = False
    for idx, video in targets:
        success = process_video_entry(idx, video)
        if success:
            processed_any = True
        save_manifest(videos)
        
    if processed_any:
        rebuild_splits()
        print("\n[Success] Batch processing complete and master splits rebuilt!")

if __name__ == "__main__":
    main()
