# Dhamma AI Training Corpus & Pipeline

A specialized, comprehensive machine learning dataset and extraction pipeline for fine-tuning Large Language Models in the authentic lineage of the **Thai Forest Tradition** (in the lineage of Luang Por Chah, Ajahn Sumedho, Ajahn Pasanno, Ajahn Amaro, and Ajahn Jayasāro).

---

## 1. Corpus Overview & Statistics

- **Total Unique Chat SFT QA Pairs**: **3,000+**
- **Training Set (`datasets/splits/train.jsonl`)**: **~2,700 records** (90%)
- **Validation Set (`datasets/splits/val.jsonl`)**: **~300 records** (10%)
- **Distinct Source Datasets**: **73 book datasets + 59 YouTube talk datasets + web page datasets**
- **Total Source Words Covered**: **~2.7+ Million Words** across 75 extracted books, 59 transcribed talks, and fetched web pages
- **Exact Duplicates**: **0** (100% deduplicated and validated)
- **Schema Compliance**: **100% Chat SFT JSONL compliant** + ShareGPT format exports

---

## 2. Pedagogical Architecture (4-Part Structure)

Every training pair follows the standard system persona and 4-part pedagogical framework:

```
System Prompt:
"You are a wise and compassionate Dhamma teacher grounded in the Thai Forest Tradition 
(in the lineage of Luang Por Chah). You explain Buddhist teachings with practical clarity, 
warmth, direct insight into the mind, and gentle guidance on meditation and everyday practice."
```

### The 4 Teaching Movements:
1. **Empathetic Acknowledgment**: Warm validation of human difficulty (*"It is natural to encounter..."*).
2. **Phenomenological Inquiry**: Direct somatic and mental investigation (*"Notice the felt sense in the body...", "Observe the silent gap between thoughts..."*).
3. **Precise Pāli Glosses**: Contextual Pali vocabulary with English translations in parentheses (*anicca, dukkha, anattā, sati, samādhi, paññā, avippaṭisāra, Buddho*).
4. **Lineage Similes & Actionable Application**: Earthy similes and tangible practice advice (*the muddy water settling, the open palm holding water, the cobra's tail*).

---

## 3. Directory Layout

```
dhamma/
├── AjhanSumedho/                     # Self-contained Ajahn Sumedho playlist pipeline
│   ├── README.md                     # Pipeline documentation
│   ├── process_playlist.py           # CLI script
│   ├── playlist_manifest.json        # Live progress tracker (59/100 completed)
│   ├── transcripts/                  # Extracted transcript text cache
│   └── datasets/                     # Per-talk Chat SFT JSONL datasets
│
├── documents/
│   ├── extracted/                    # 75 extracted EPUB/PDF book directories
│   ├── youtube_playlists/            # Multi-playlist registry and manifests
│   │   ├── playlists_registry.json   # Master registry of all registered playlists
│   │   └── *_manifest.json           # Per-playlist state files
│   ├── youtube_transcripts/          # Central transcript repository
│   └── web_pages/                    # Fetched & cleaned web page text files
│       └── web_registry.json         # Registry of all processed web pages
│
├── datasets/                         # Individual book, talk, and web page datasets (.jsonl)
│   ├── web_pages/                    # Per-page Chat SFT datasets (web source)
│   ├── splits/                       # Master splits: master_dhamma_qa, train, val
│   └── exports/                      # ShareGPT format JSON exports
│
├── tools/
│   ├── web_page_pipeline.py          # ← NEW: Web page → training data pipeline
│   ├── playlist_pipeline.py          # Universal YouTube playlist manager
│   └── regen_yt_qa.py                # Transcript-grounded QA regenerator
│
├── audit_structure.py                # 4-part pedagogical structure auditor
├── check_duplicates.py               # Fast semantic & exact duplicate detector
├── clean_datasets.py                 # Automated deduplication cleaner
├── corpus_summary.py                 # Source-to-dataset coverage summary tool
├── export_formats.py                 # ShareGPT/Alpaca format exporter
├── fill_gaps.py                      # Automated chapter & concept gap filler
├── merge_and_split_dataset.py        # Master merge, split (90/10) & schema validator
└── validate_coverage.py              # Two-layer chapter & Pāli concept coverage auditor
```

---

## 4. Web Page Pipeline ← NEW

Fetch any Dhamma web page (dhammatalks.org, accesstoinsight.org, etc.) and generate
grounded QA training pairs tied directly to that page's actual content.

```bash
# Process a complete online book via Table of Contents (crawls all chapters/sections automatically)
python tools/web_page_pipeline.py --book https://www.dhammatalks.org/books/HeartReleased/

# Process a single URL
python tools/web_page_pipeline.py --add https://www.dhammatalks.org/books/HeartReleased/Section0005.html

# Process multiple individual URLs at once
python tools/web_page_pipeline.py --add URL1 URL2 URL3

# Process a batch from a text file (one URL per line, # = comment)
python tools/web_page_pipeline.py --file urls.txt

# List all registered pages and their QA count
python tools/web_page_pipeline.py --list

# Check if a URL was already processed
python tools/web_page_pipeline.py --check https://...

# Force re-fetch and regenerate a specific URL
python tools/web_page_pipeline.py --reprocess https://...

# Show summary statistics
python tools/web_page_pipeline.py --status
```

### How it works:
1. **Fetches** raw HTML with retry logic and browser-like User-Agent headers.
2. **Extracts** main content body (strips nav, header, footer, scripts) via a custom HTML parser targeting `<main>`, `#content`, and `<h2>` section headings.
3. **Detects** named `§ N. Title` sections and 40+ Pāli keyword triggers.
4. **Generates** 8–15 grounded QA pairs — every answer opens with an actual quoted sentence from the fetched page.
5. **Saves** per-page JSONL dataset to `datasets/web_pages/<slug>_qa.jsonl`.
6. **Rebuilds** master train/val splits automatically.

### Storage:
| Item | Location |
|---|---|
| Raw text | `documents/web_pages/<slug>.txt` |
| QA dataset | `datasets/web_pages/<slug>_qa.jsonl` |
| Merged into master | `datasets/<slug>_qa.jsonl` |
| Registry | `documents/web_pages/web_registry.json` |

---

## 5. Universal YouTube Playlist Pipeline

Register, track, and incrementally process **any YouTube playlist**:

```bash
# Register a new playlist
python tools/playlist_pipeline.py --add "<YOUTUBE_PLAYLIST_URL>" --name "Playlist Title"

# View all playlists and completion progress
python tools/playlist_pipeline.py --list

# Process the next N pending talks (extracts transcripts, generates QA, rebuilds splits)
python tools/playlist_pipeline.py --playlist <PLAYLIST_KEY> --count 5

# Process a specific video range (1-indexed)
python tools/playlist_pipeline.py --playlist <PLAYLIST_KEY> --range 1 10
```

---

## 6. Core Pipeline Commands

```bash
# Audit pedagogical structure & Pāli term density across all datasets
python audit_structure.py

# Check for exact or near-duplicate questions (Jaccard n-gram similarity)
python check_duplicates.py

# Validate topic and chapter coverage against all 75 extracted source books
python validate_coverage.py

# Re-merge all datasets and rebuild train/val splits
python merge_and_split_dataset.py --val-ratio 0.1 --output-dir datasets/splits

# Export master splits to ShareGPT format
python export_formats.py --all-splits -f sharegpt

# Generate full corpus health summary
python corpus_summary.py
```
