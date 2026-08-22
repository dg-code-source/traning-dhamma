# Walkthrough: Unified Dhamma Pipeline (YouTube & EPUB to Chat SFT Datasets)

The automated pipeline in [`dhamma/`](file:///c:/training-dhamma/dhamma/) now fully supports both **YouTube Dhamma talks** and **EPUB Dhamma books**, converting them into validated Chat SFT training datasets for LLMs.

---

## 1. Directory Structure

```
c:\training-dhamma\dhamma\
├── documents/
│   ├── raw_epubs/            # Stored original .epub files
│   └── extracted/<book_name>/# Extracted chapters, full_book.txt, and metadata.json
├── transcripts/              # Extracted YouTube transcripts (*.txt)
├── datasets/                 # Generated Chat SFT JSONL training pairs (*.jsonl)
├── extract_epub.py           # EPUB book extractor and metadata parser
├── extract_transcript.py     # YouTube transcript extractor & cleaner
├── verify_dataset.py         # JSONL schema and content validator
├── RULES.md                  # Unified persona rules, Pāli terms, and SOP
├── requirements.txt          # Python dependencies (youtube-transcript-api, beautifulsoup4, ebooklib)
├── README.md                 # Documentation & quickstart guide
└── WALKTHROUGH.md            # Execution summary
```

---

## 2. Tested Workflows

### A. YouTube Video Processing
- Extractor: `python dhamma/extract_transcript.py "<YOUTUBE_URL>"`
- Example: [`dhamma/datasets/Luang Por Viradhammo - Reflections on the Dhamma, Seeking Happiness_qa.jsonl`](file:///c:/training-dhamma/dhamma/datasets/Luang%20Por%20Viradhammo%20-%20Reflections%20on%20the%20Dhamma,%20Seeking%20Happiness_qa.jsonl) (18 pairs).

### B. EPUB Document Processing
- Extractor: `python dhamma/extract_epub.py "<path_to_epub>"`
- Output folder: `dhamma/documents/extracted/<Book Title - Author>/`
  - `metadata.json` (Title, Author, Chapter index, Word counts)
  - `chapter_01_<title>.txt`, `chapter_02_<title>.txt`, ...
  - `full_book.txt`
- Dataset generation: Process either whole books or individual chapters into `dhamma/datasets/`.

---

## 3. Schema & Validation

All generated datasets adhere to the Chat SFT specification:
```json
{
  "messages": [
    {"role": "system", "content": "You are a wise and compassionate Dhamma teacher grounded in the Thai Forest Tradition..."},
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```
Validation command: `python dhamma/verify_dataset.py "dhamma/datasets/<file>.jsonl"`.
