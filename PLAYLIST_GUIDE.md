# Multi-Playlist YouTube Pipeline Documentation

The generalized pipeline allows you to register **any YouTube playlist**, extract transcripts, generate grounded 4-part Thai Forest training pairs, and automatically update master training splits.

---

## 1. Quick CLI Reference

```bash
# 1. Register any new YouTube playlist:
python tools/playlist_pipeline.py --add "https://www.youtube.com/playlist?list=PLAYLIST_ID" --name "Ajahn Pasanno Dhamma Talks"

# 2. List all registered playlists and view live completion progress:
python tools/playlist_pipeline.py --list

# 3. Process the next N pending talks from a playlist:
python tools/playlist_pipeline.py --playlist ajahn_sumedho_dhamma_talks_reflections --count 5

# 4. Process a specific range of talks (e.g. videos 10 to 20):
python tools/playlist_pipeline.py --playlist ajahn_sumedho_dhamma_talks_reflections --range 10 20

# 5. Customize the polite request delay to avoid YouTube rate limits:
python tools/playlist_pipeline.py --playlist ajahn_sumedho_dhamma_talks_reflections --count 10 --delay 3.0
```

---

## 2. Directory Layout & Persistence

```
dhamma/
├── documents/
│   ├── youtube_playlists/
│   │   ├── playlists_registry.json                # Master registry of all added playlists
│   │   └── {playlist_slug}_manifest.json          # State tracker for each playlist (100% persistent)
│   └── youtube_transcripts/
│       └── yt_{playlist_slug}_{idx:03d}_{title}.txt # Extracted raw transcripts
├── datasets/
│   └── yt_{playlist_slug}_{idx:03d}_{title}_qa.jsonl # Standalone Chat SFT dataset per talk
├── datasets/splits/
│   ├── master_dhamma_qa.jsonl                     # Automatically re-merged master
│   ├── train.jsonl                                # 90% training split
│   └── val.jsonl                                  # 10% validation split
└── tools/
    └── playlist_pipeline.py                       # Universal CLI tool
```

---

## 3. What You Can Say in Chat:

You can provide any YouTube playlist link in chat:

- *"Here is another playlist: `https://www.youtube.com/playlist?list=...`. Please add it and process the first 5 videos."*
- *"Process the next 10 videos from Ajahn Sumedho playlist."*
- *"List all my playlists and show progress."*
