# Ajahn Sumedho YouTube Playlist Pipeline

This directory contains the self-contained, end-to-end, incremental extraction and QA training pair generator for the **Ajahn Sumedho Dhamma Talks & Reflections** YouTube playlist:
`https://www.youtube.com/playlist?list=PL--llepYBCu4lh112KIeRZ75keS_283ox`

---

## 1. Directory Structure

```
AjhanSumedho/
├── README.md                          # Architecture & usage instructions
├── process_playlist.py                # Main executable CLI engine
├── playlist_manifest.json             # Persistent state tracker (100 video entries)
├── transcripts/                       # Raw text transcripts extracted per video
│   └── {idx:03d}_{slug}.txt
└── datasets/                          # Per-video Chat SFT QA datasets
    └── yt_sumedho_{idx:03d}_{slug}_qa.jsonl
```

---

## 2. CLI Usage (Works from Cold Start)

You can run `process_playlist.py` from a cold start. It will automatically initialize the playlist manifest if missing and process whatever range you request.

```bash
# Process the next N unprocessed videos from wherever it left off:
python AjhanSumedho/process_playlist.py --count 5

# Process a specific index range (1-indexed):
python AjhanSumedho/process_playlist.py --range 1 10

# Process a single video:
python AjhanSumedho/process_playlist.py --range 1 1

# Check current progress status:
python AjhanSumedho/process_playlist.py --status

# Re-sync / refresh the playlist video list:
python AjhanSumedho/process_playlist.py --sync
```

---

## 3. Automated Processing Per Video

1. **Transcript Fetching**: Pulls full text captions with timing via `youtube_transcript_api`.
2. **Transcript Cleaning**: Formats raw speech into clean, readable paragraphs stored at `AjhanSumedho/transcripts/`.
3. **4-Part Thai Forest QA Synthesis**: Generates 5–10 grounded training pairs per talk following the strict pedagogical structure:
   - Empathetic Acknowledgment
   - Phenomenological Inquiry (*Buddho*, felt sense in body, observing the silent gap)
   - Precise Pāli glosses (*dukkha*, *anicca*, *anattā*, *sati*, *avippaṭisāra*, etc.)
   - Lineage similes & actionable application
4. **Dataset Creation**: Saved to both `AjhanSumedho/datasets/` and the master `datasets/` folder.
5. **Auto-Rebuild**: Automatically calls `merge_and_split_dataset.py` and `export_formats.py` to keep the master corpus synchronized.
