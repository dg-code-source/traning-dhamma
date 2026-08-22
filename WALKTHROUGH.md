# Walkthrough: Dhamma Training Pipeline

The pipeline in [`dhamma/`](file:///c:/training-dhamma/dhamma/) converts Dhamma talks (YouTube) and books (EPUB/PDF) into validated Chat SFT training datasets for LLMs, following the Thai Forest Tradition teacher persona defined in [RULES.md](file:///c:/training-dhamma/dhamma/RULES.md).

---

## Current Corpus State

| Dataset | Source | QA Pairs | Avg Words |
|---|---|---|---|
| `Daughters_and_Sons_qa.jsonl` | EPUB – Ajahn Jayasaro | 15 | 194 |
| `In_Simple_Terms_Similes_qa.jsonl` | EPUB – Ajahn Chah | 53 | 113 |
| `Knowing the mood of the mind_qa.jsonl` | YouTube – Ajahn Viradhammo | 18 | 118 |
| `Luang Por Viradhammo - Reflections..._qa.jsonl` | YouTube – Ajahn Viradhammo | 18 | 108 |
| `Mindfulness_Precepts_and_Crashing..._qa.jsonl` | EPUB – Ajahn Jayasaro | 18 | 110 |
| `Seen_in_Their_True_Light_qa.jsonl` | EPUB – Thai Forest Tradition | 23 | 116 |
| `Stillness_Flowing_qa.jsonl` | EPUB – Ajahn Jayasaro | 36 | 120 |
| `The_Contemplatives_Companion_qa.jsonl` | EPUB – Ajahn Viradhammo | 84 | 131 |
| `The_Contemplatives_Craft_qa.jsonl` | EPUB – Ajahn Viradhammo | 90 | 112 |
| `The_Real_Practice_qa.jsonl` | PDF – Ajahn Jayasaro | 18 | 113 |
| `The_Stillness_of_Being_qa.jsonl` | EPUB – Ajahn Viradhammo | 78 | 92 |
| `Without_and_Within_qa.jsonl` | EPUB – Ajahn Jayasaro | 120 | 188 |
| **TOTAL** | | **571** | **131** |

**Splits**: train 514 / val 57  
**Exports**: `datasets/exports/` — ShareGPT format for all splits

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
