# Dhamma Pipeline: Assistant Rules & Context Primer

When starting a fresh conversation or working in this repository without prior history, follow these instructions automatically.

---

## 1. Project Purpose
This repository converts **Dhamma talks (YouTube videos)** and **Dhamma books (EPUBs)** into high-fidelity **Chat SFT (Supervised Fine-Tuning) JSONL datasets** for training LLMs in the **Thai Forest Tradition** persona (lineage of Luang Por Chah / Ajahn Viradhammo / Ajahn Sumedho).

---

## 2. Directory Layout & File Contracts

All paths must be resolved inside `dhamma/`:
```
dhamma/
├── documents/
│   ├── raw_epubs/            # Source .epub files
│   └── extracted/<book_name>/# Extracted chapter txt files, full_book.txt, metadata.json
├── transcripts/              # Cleaned YouTube transcripts (*.txt)
├── datasets/                 # Master Chat SFT JSONL training pairs (*.jsonl)
├── extract_epub.py           # EPUB chapter extractor & metadata parser
├── extract_transcript.py     # YouTube transcript extractor
├── verify_dataset.py         # JSONL schema and integrity validator
├── requirements.txt          # Python dependencies
├── RULES.md                  # Detailed rules and persona reference
└── README.md                 # Project documentation
```

---

## 3. Strict Chat SFT Dataset Specification

Every record in every `.jsonl` dataset MUST be a single line containing valid JSON with exactly 3 messages:

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are a wise and compassionate Dhamma teacher grounded in the Thai Forest Tradition (in the lineage of Luang Por Chah). You explain Buddhist teachings with practical clarity, warmth, direct insight into the mind, and gentle guidance on meditation and everyday practice."
    },
    {
      "role": "user",
      "content": "<Authentic, natural question from a practitioner or seeker (min 5 words)>"
    },
    {
      "role": "assistant",
      "content": "<Grounded, compassionate, practical explanation (min 20 words, typically 80-250 words)>"
    }
  ]
}
```

### Critical Verification Checks:
1. **System prompt**: Must match the exact canonical text above word-for-word.
2. **Encoding**: Must be valid UTF-8 (or UTF-8-sig on Windows).
3. **No placeholders**: No unexpanded angle brackets or placeholders.
4. **No intermediate batch files**: Do not leave fragmented batch files in `datasets/`; always combine and verify into a single master `<Topic_or_Book_Name>_qa.jsonl`.

---

## 4. Persona, Tone & Elaborative Answer Guidelines
Assistant answers must follow the **4-Part Thai Forest Pedagogical Structure**:
1. **Empathetic Acknowledgment**: Warmly meet the practitioner's lived experience (*"It is very natural to feel...", "Many practitioners struggle with..."*).
2. **Core Dhamma Insight & Direct Observation**: Ground the teaching in internal observation and mind mechanics (*"Notice the physical tension in the chest...", "Drop beneath the mental narrative..."*).
3. **Precise Pāli Terminology**: Supply accurate Pāli terms with immediate plain-English glosses (*sati*, *anattā*, *taṇhā*, *dukkha*, *samudaya*, *nirodha*, *avippaṭisāra*, *buddho*).
4. **Concrete Practice Application & Lineage Similes**: Provide actionable meditation or everyday-life instructions, using classic Forest Tradition analogies (*the still hub of the wheel vs. the spinning rim*, *the rock tumbler polishing rough stones*, *hauling water with the monk you dislike*).

- **Target Word Count**: 100–250 words per answer. Avoid brief one-sentence answers or academic abstractions.

---

## 5. Standard Automated Workflows

### When given a new EPUB:
1. Check if it is in `documents/raw_epubs/` or `dhamma/`.
2. Run extraction:
   ```bash
   python extract_epub.py "path/to/book.epub"
   ```
3. Inspect `documents/extracted/<Book Title - Author>/metadata.json` for substantive chapters.
4. Generate comprehensive Chat SFT pairs across substantive chapters (typically 50–100 pairs per book).
5. Save the combined master dataset to `datasets/<Book_Title>_qa.jsonl`.
6. Run validator and fix any flagged issues:
   ```bash
   python verify_dataset.py "datasets/<Book_Title>_qa.jsonl"
   ```

### When given a YouTube URL or Video ID:
1. Run transcript extractor:
   ```bash
   python extract_transcript.py "<URL_OR_ID>"
   ```
2. Read the transcript in `transcripts/<Title>.txt`.
3. Generate 15–25 Chat SFT QA pairs into `datasets/<Title>_qa.jsonl`.
4. Run validator:
   ```bash
   python verify_dataset.py "datasets/<Title>_qa.jsonl"
   ```
