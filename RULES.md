# Dhamma QA Training Pipeline: Rules & Specification

This document defines the rules, persona guidelines, schema standards, and operating procedure for converting Dhamma talk transcripts (YouTube) and Dhamma books (EPUB) into LLM training datasets.

---

## 1. System Prompt & Persona

Every entry in every dataset must use the following standard system prompt:

```
You are a wise and compassionate Dhamma teacher grounded in the Thai Forest Tradition (in the lineage of Luang Por Chah). You explain Buddhist teachings with practical clarity, warmth, direct insight into the mind, and gentle guidance on meditation and everyday practice.
```

### Voice & Pedagogical Tone Guidelines
- **Grounded & Compassionate**: Speak as an experienced meditation teacher addressing real human dilemmas with warmth and clarity.
- **Rooted in Experience over Dogma**: Emphasize direct observation ("It's like this", noticing the silent gap, investigating the physical feel in the heart) rather than intellectual abstractions.
- **Precise Dhamma Terminology**: Use key Pāli terms accurately with plain-English contextual explanations:
  - *Ahaṅkāra* ("I-making") & *Mamiṅkāra* ("My-making")
  - *Māna* (Conceit / measuring oneself against others or standards)
  - *Papañca* (Mental proliferation and narrative spinning)
  - *Sati* (Mindfulness / seeing mental states as objects)
  - *Dukkha*, *Samudaya*, *Nirodha*, *Magga* (Four Noble Truths)
  - *Avippaṭisāra* (Freedom from remorse born of moral integrity)
  - *Buddho* (The awake, knowing presence)
  - *Anicca Saññā* (Perception of impermanence/change)
  - *Anupādāna* (Non-attachment / non-grasping)

---

## 2. Dataset Schema (Chat SFT JSONL)

Target output format is newline-delimited JSON (`.jsonl`), where each row is an independent valid JSON object conforming to the Chat SFT specification:

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are a wise and compassionate Dhamma teacher grounded in the Thai Forest Tradition (in the lineage of Luang Por Chah). You explain Buddhist teachings with practical clarity, warmth, direct insight into the mind, and gentle guidance on meditation and everyday practice."
    },
    {
      "role": "user",
      "content": "<Clear, authentic question from a practitioner or seeker>"
    },
    {
      "role": "assistant",
      "content": "<Comprehensive, compassionate, practical Dhamma explanation>"
    }
  ]
}
```

---

## 3. Directory Layout

```
dhamma/
├── .agent/rules/                     # Auto-loaded assistant rules
├── .cursor/rules/                    # IDE agent rules
├── documents/
│   ├── raw_epubs/                    # Uploaded / downloaded .epub files
│   ├── raw_pdfs/                     # Uploaded / downloaded .pdf files
│   └── extracted/<book_name>/        # Extracted contents per book:
│       ├── metadata.json             # Title, Author, TOC, Chapter stats
│       ├── full_book.txt             # Concatenated book text
│       ├── chapter_01_<title>.txt    # Individual chapter text
│       └── ...
├── transcripts/                      # YouTube transcripts (*.txt)
├── datasets/                         # Generated Chat SFT JSONL datasets (*.jsonl)
├── build_dataset.py                  # Standardized Chat SFT dataset builder
├── merge_and_split_dataset.py        # Dataset merger, deduplicator & train/val splitter
├── export_formats.py                 # Format converter (ShareGPT, Alpaca)
├── corpus_summary.py                 # Corpus inventory & health check
├── eval_prompts.py                   # Post-training evaluation benchmark suite
├── extract_epub.py                   # EPUB book extractor & metadata parser
├── extract_pdf.py                    # PDF book extractor & metadata parser
├── extract_transcript.py             # YouTube transcript extractor
├── verify_dataset.py                 # JSONL schema and integrity validator
├── requirements.txt                  # Python dependencies
├── RULES.md                          # This specification
└── README.md                         # Quickstart documentation
```

---

## 4. Standard Operating Procedures (SOP)

### A. YouTube Video Workflow
1. **Extract**: `python dhamma/extract_transcript.py "<YOUTUBE_URL>"`
2. **Review**: Check `dhamma/transcripts/<title>.txt`.
3. **Generate QA Pairs**: Create 15–25 Chat SFT QA pairs in `dhamma/datasets/<title>_qa.jsonl`.
4. **Verify**: `python dhamma/verify_dataset.py "dhamma/datasets/<title>_qa.jsonl"`.

### B. EPUB Document Workflow
1. **Extract**: `python dhamma/extract_epub.py "<path_to_epub>"`
   - Automatically saves copy to `dhamma/documents/raw_epubs/`.
   - Extracts chapter texts, `full_book.txt`, and `metadata.json` into `dhamma/documents/extracted/<book_name>/`.
2. **Generate QA Pairs**:
   - For a full book: process all substantive chapters into `dhamma/datasets/<book_name>_qa.jsonl` (typically 50–100 pairs per book).
   - If generating in parallel batches, always merge into a single master file and remove intermediate batch files.
3. **Verify**: `python dhamma/verify_dataset.py "dhamma/datasets/<dataset_name>.jsonl"`.

---

## 5. QA Quality Guidelines

### A. Answer Quality
- **Minimum length**: Assistant answers must be at least 20 words. Aim for 80–250 words for substantive teachings.
- **Faithfulness**: Answers must be grounded in the source material (transcript or book chapter). Do NOT fabricate quotes, suttas, or attributions not present in the source.
- **Pāli terms**: When using Pāli terms, always provide a brief English gloss on first use (e.g., *sati* (mindfulness)).
- **Practical emphasis**: Include concrete meditation instructions or everyday-life applications where the source supports it.

### B. Question Quality
- **Minimum length**: User questions must be at least 5 words.
- **Diversity**: Across a dataset, questions should span different types:
  - Conceptual ("What is...?", "How does X relate to Y?")
  - Practical ("How do I practice...?", "What should I do when...?")
  - Experiential ("What does it feel like when...?", "How do I know if...?")
  - Clarifying ("Can you explain the difference between...?")
- **Authenticity**: Questions should sound like a genuine practitioner or seeker, not a quiz question.

### C. Dataset Integrity
- **No duplicates**: Each QA pair must be unique within the dataset. No repeated questions or answers.
- **System prompt**: Every record MUST include the exact system prompt from Section 1 as the first message.
- **Single-turn only**: Each record must contain exactly 3 messages: `["system", "user", "assistant"]`. Multi-turn conversations are not supported by the current schema.
- **JSON validity**: Each line must be a self-contained, valid JSON object. No trailing commas, no comments.
- **No template placeholders**: No `<angle bracket placeholders>` should remain in final output.

---

## 6. Fresh Agent Startup Protocol

Whenever an agent begins a new conversation or context without prior chat history, it should automatically:
1. Identify the input source (EPUB in `documents/raw_epubs/` or YouTube URL).
2. Check `documents/extracted/` or `transcripts/` to avoid re-extracting already parsed files.
3. Generate grounded Chat SFT pairs conforming to Section 1–2.
4. Save directly into `datasets/<Subject_or_Book>_qa.jsonl`.
5. Run `python verify_dataset.py "datasets/<dataset>.jsonl"` and confirm all records pass before concluding.
