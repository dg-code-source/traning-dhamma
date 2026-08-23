# Walkthrough: Dhamma Training Pipeline

The pipeline in [`dhamma/`](file:///c:/training-dhamma/dhamma/) converts Dhamma talks (YouTube) and books (EPUB/PDF) into validated Chat SFT training datasets for LLMs, following the Thai Forest Tradition teacher persona defined in [RULES.md](file:///c:/training-dhamma/dhamma/RULES.md).

---

## Current Corpus State

- **Total QA Pairs**: **1,618 records across 38 source datasets**
- **Total Training Words**: ~214,943 words (~290,173 tokens)
- **Average Assistant Words**: ~133 words per answer
- **Splits**: train 1,457 (90%) / val 161 (10%)
- **Exports**: `datasets/exports/` — ShareGPT format for master, train, and val splits
- **Quality Gates**:
  - `python verify_dataset.py <file>` (Schema & length validation)
  - `python audit_structure.py --all-datasets` (4-part Thai Forest pedagogical compliance)
  - `python check_duplicates.py` (Exact & near-duplicate semantic analysis)

---

## Standard Workflow for a New Source

### 1. Extract the Source
```bash
# EPUB
python extract_epub.py "documents/raw_epubs/<book>.epub"

# PDF
python extract_pdf.py "documents/raw_pdfs/<book>.pdf"

# YouTube
python extract_transcript.py "<youtube_url>"
```

### 2. Inspect Extracted Content
Review chapters in `documents/extracted/<Book - Author>/` to understand structure, themes, and unique content before generating QA pairs.

### 3. Generate QA Pairs
Write a Python script in `scratch/` (or use Antigravity chat) to produce a `datasets/<Source>_qa.jsonl` file following the 4-part pedagogical structure in `RULES.md`:
- Empathetic acknowledgment
- Phenomenological insight
- Pāli terminology with gloss
- Lineage simile and concrete application

### 4. Verify
```bash
python verify_dataset.py "datasets/<Source>_qa.jsonl"
```
Must pass with all 3 messages per record and the exact system prompt from `RULES.md`.

### 5. Add to `corpus_summary.py` custom_map
If the book title does not automatically match the dataset filename, add an entry to `custom_map` in `corpus_summary.py`.

### 6. Rebuild Splits and Exports
```bash
python merge_and_split_dataset.py
python export_formats.py --all-splits -f sharegpt
python corpus_summary.py   # Confirm [HEALTHY] status
```

### 7. Commit and Push
```bash
git add datasets/ corpus_summary.py; git commit -m "Add <Source> QA dataset"; git push
```

---

## Schema

All records use the Chat SFT format:
```json
{
  "messages": [
    {"role": "system", "content": "You are a wise and compassionate Dhamma teacher..."},
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```

---

## Health Audit

Run `python corpus_summary.py` at any time for the full corpus health table. Status badges:
- `[HEALTHY]` — Good pair count and answer depth
- `[NEEDS DEPTH]` — Too few pairs for source size
- `[ANSWERS BRIEF]` — Assistant answers averaging under 80 words
- `[MISSING QA]` — Extracted source has no dataset yet
