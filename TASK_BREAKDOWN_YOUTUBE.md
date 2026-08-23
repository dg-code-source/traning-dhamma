# Granular Task Breakdown: YouTube Playlist Incremental Pipeline

## TASK 1: Initialize Manifest & Extract All 100 Video Entries
- Build `sync_playlist_manifest()` to fetch all video IDs and titles from playlist URL `PL--llepYBCu4lh112KIeRZ75keS_283ox`.
- Save state to `documents/youtube_playlists/ajahn_sumedho_playlist.json`.

## TASK 2: Build `process_playlist.py` Core Engine
- Transcript fetching via `youtube_transcript_api`.
- Transcript formatting and saving to `documents/youtube_transcripts/`.
- Dynamic 4-part Thai Forest QA pair synthesis (5–10 pairs per talk).
- Dataset saving to `datasets/yt_sumedho_{idx}_{slug}_qa.jsonl`.
- CLI commands: `--count N`, `--range START END`, `--status`, `--sync-playlist`.

## TASK 3: Master Split Auto-Rebuild Integration
- After processing batch, automatically execute:
  1. `merge_and_split_dataset.py --val-ratio 0.1 --output-dir datasets/splits`
  2. `export_formats.py --all-splits -f sharegpt`
  3. `corpus_summary.py` custom map synchronization

## TASK 4: Verification & Test Run
- Run test on Video 1 (`--range 1 1`).
- Verify QA quality, structure, and schema compliance.
