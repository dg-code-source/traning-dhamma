# Granular Task Breakdown: Independent Validation & Gap-Fill

> Each task below is self-contained with exact file paths, data formats, and precise instructions.

---

## TASK 1: Build `validate_coverage.py` — The Analysis Engine

**File**: `c:\training-dhamma\dhamma\validate_coverage.py`

### 1.1 — Imports & Constants

```python
import os, sys, json, re, glob
from collections import Counter, defaultdict
```

Add UTF-8 stdout reconfiguration:
```python
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
```

Define constants:
- `EXTRACTED_DIR = "documents/extracted"`
- `DATASETS_DIR = "datasets"`
- `REPORT_JSON = "datasets/coverage_report.json"`
- `REPORT_MD = "datasets/coverage_report.md"`

### 1.2 — Define the Book-to-Dataset Mapping

Copy the **exact** `custom_map` dictionary from [`corpus_summary.py`](file:///c:/training-dhamma/dhamma/corpus_summary.py) lines 122–177. This maps source book titles (from `metadata.json`) to dataset filenames.

Also implement the **fuzzy fallback** matching logic from `corpus_summary.py` lines 187–192:
```python
clean_df = df.lower().replace("_", " ").replace(" qa.jsonl", "").replace(".jsonl", "")
clean_bm = title.lower().replace("'", "").replace("\u2019", "")
if clean_bm == clean_df or clean_df in clean_bm:
    matched = True
```

The function should return a list of dicts:
```python
[
  {
    "book_title": "Small Boat, Great Mountain",
    "book_dir": "Small Boat, Great Mountain - Ajahn Amaro",
    "total_words": 49683,
    "chapters": [{"title": "1. Ultimate and Conventional Reality", "word_count": 3448, "file": "chapter_01_..."}, ...],
    "dataset_file": "Small_Boat_Great_Mountain_qa.jsonl",  # or None if MISSING QA
    "dataset_path": "datasets/Small_Boat_Great_Mountain_qa.jsonl"  # or None
  },
  ...
]
```

### 1.3 — Define Non-Substantive Chapter Title Patterns

Build a list of chapter titles to **skip** (they don't need QA pairs):
```python
SKIP_PATTERNS = [
    r"^copyright", r"^acknowledgement", r"^glossary", r"^preface",
    r"^contents", r"^abbreviation", r"^note to the reader",
    r"^further resource", r"^about the author", r"^foreword",
    r"^introduction$", r"^blank page", r"^selected chant",
    r"^appendix", r"^index", r"^bibliography", r"^dedication",
    r"^bio\.pdf", r"^cover", r"^title page",
]
```

A chapter is **substantive** if:
- Its title does NOT match any skip pattern (case-insensitive regex)
- Its `word_count` >= 200

### 1.4 — Layer 1: Chapter Coverage Analysis Function

```python
def analyze_chapter_coverage(book_info: dict) -> dict:
```

**Inputs**: A single book info dict from 1.2.

**Logic**:
1. Get list of substantive chapters (filter using 1.3 rules).
2. If `dataset_file` is None, return `{"status": "MISSING_QA", "substantive_chapters": [...], "covered": [], "uncovered": [...]}`.
3. Load all QA pairs from the dataset `.jsonl` file. For each pair, concatenate `question + " " + answer` into a single search string.
4. For each substantive chapter title, extract **core keywords** by:
   - Stripping leading numbering (e.g., "1.", "Chapter 12", "Part 2")
   - Lowercasing
   - Splitting into words
   - Removing common English stop words (the, a, an, of, in, to, and, is, it, for, with, on, at, by, from, as, or, that, this, but, be)
5. A chapter is **covered** if at least 40% of its core keywords appear in at least one QA pair's combined text (case-insensitive substring search).
6. Return:
```python
{
    "total_substantive": int,
    "covered_count": int,
    "uncovered_count": int,
    "coverage_pct": float,
    "covered_chapters": ["1. Ultimate and Conventional Reality", ...],
    "uncovered_chapters": [
        {"title": "7. Off the Wheel", "word_count": 7593, "file": "chapter_07_7. Off the Wheel.txt"},
        ...
    ]
}
```

### 1.5 — Define Pāli Terms Master List

Hardcode a comprehensive Pāli terms list for keyword scanning:

```python
PALI_TERMS = [
    "anicca", "dukkha", "anatta", "anattā", "tanha", "taṇhā",
    "sati", "samadhi", "samādhi", "panna", "paññā", "sila", "sīla",
    "metta", "mettā", "karuna", "karuṇā", "mudita", "muditā",
    "upekkha", "upekkhā", "nibbana", "nibbāna", "sankhara", "saṅkhāra",
    "vipassana", "vipassanā", "jhana", "jhāna", "kamma",
    "bhavana", "bhāvanā", "papanca", "papañca", "sunnata", "suññatā",
    "piti", "pīti", "sukha", "vedana", "vedanā", "samsara", "saṃsāra",
    "paticca samuppada", "paṭicca-samuppāda", "cetana", "cetanā",
    "avijja", "avijjā", "lobha", "dosa", "moha", "khanti",
    "nekkhamma", "adhitthana", "adhiṭṭhāna", "viriya",
    "sacca", "anapanasati", "ānāpānasati", "brahmavihara", "brahmavihāra",
    "kilesa", "vinaya", "dhamma", "sangha", "saṅgha", "buddha", "buddho",
    "nirodha", "magga", "samudaya", "raga", "rāga", "bhava",
    "upadana", "upādāna", "phassa", "nama-rupa", "nāma-rūpa",
    "ayatana", "āyatana", "khandha", "citta", "mano", "vinnana", "viññāṇa",
    "bojjhanga", "bojjhaṅga", "arahant", "bodhisatta",
    "dana", "dāna", "patimokkha", "pātimokkha",
    "nivarana", "nīvaraṇa", "kamacchanda", "kāmacchanda",
    "byapada", "byāpāda", "thina-middha", "uddhacca",
    "vicikiccha", "vicikicchā", "saddha", "saddhā",
    "mana", "māna", "avippatiisara", "avippaṭisāra",
    "ahankara", "ahaṅkāra", "maminkara", "mamiṅkāra",
    "atammayata", "atammayatā", "appamada", "appamāda",
]
```

### 1.6 — Layer 2: Keyword/Concept Coverage Function

```python
def analyze_keyword_coverage(book_info: dict) -> dict:
```

**Inputs**: A single book info dict from 1.2.

**Logic**:
1. Read the source book's `full_book.txt` from `documents/extracted/<book_dir>/full_book.txt`.
2. Lowercase the entire text.
3. For each Pāli term in `PALI_TERMS`, count occurrences in the source text. A term is **significant** if it appears >= 3 times.
4. If `dataset_file` is None, return all significant terms as missing.
5. Concatenate ALL QA pairs from the dataset into one big string (questions + answers).
6. For each significant Pāli term, check if it appears in the QA concatenation (case-insensitive).
7. Return:
```python
{
    "significant_pali_in_source": ["sati", "dukkha", "metta", ...],
    "pali_covered_in_qa": ["sati", "dukkha", ...],
    "pali_missing_from_qa": ["metta", ...],
    "pali_coverage_pct": float
}
```

### 1.7 — Main Execution & Report Generation

```python
def main():
```

1. Build the book-to-dataset mapping (1.2).
2. For each mapped book, run `analyze_chapter_coverage()` and `analyze_keyword_coverage()`.
3. Collect results into a list of dicts.
4. Save the full results as `datasets/coverage_report.json`.
5. Generate a human-readable markdown report `datasets/coverage_report.md` with:
   - A summary table (book title | chapters | covered | uncovered | ch coverage % | pāli coverage %)
   - A per-book detail section listing uncovered chapter titles and missing Pāli terms
   - A section listing all `[MISSING QA]` books with > 10,000 words that need new datasets
6. Print a summary to stdout.

---

## TASK 2: Run the Validation Analysis

**Command**: `python validate_coverage.py`
**Working directory**: `c:\training-dhamma\dhamma`
**Expected output files**:
- `c:\training-dhamma\dhamma\datasets\coverage_report.json`
- `c:\training-dhamma\dhamma\datasets\coverage_report.md`

**Expected runtime**: < 30 seconds (all local file I/O, no network).

---

## TASK 3: Generate Gap-Filling QA Pairs for Existing Datasets

For each existing dataset that has uncovered chapters or missing Pāli concepts (from the coverage report):

### 3.1 — Create `fill_gaps.py`

**File**: `c:\training-dhamma\dhamma\fill_gaps.py`

This script:
1. Reads `datasets/coverage_report.json`.
2. For each book with `dataset_file != None` and uncovered chapters:
   - Reads the actual chapter text from `documents/extracted/<book_dir>/<chapter_file>`.
   - Extracts the first 500 words of the chapter to understand its theme.
   - Generates **1–2 QA pairs per uncovered chapter** that are grounded in the chapter's actual content.
3. For each book with missing Pāli terms:
   - Generates **1 QA pair per missing significant Pāli term**, tying it to the book's specific context.
4. Appends new pairs to the existing `.jsonl` dataset files (not overwriting).

**QA Generation Format** — Every generated pair MUST:
- Use the exact system prompt from `RULES.md` line 12:
  ```
  You are a wise and compassionate Dhamma teacher grounded in the Thai Forest Tradition (in the lineage of Luang Por Chah). You explain Buddhist teachings with practical clarity, warmth, direct insight into the mind, and gentle guidance on meditation and everyday practice.
  ```
- Follow the 4-part Thai Forest structure:
  1. Empathetic acknowledgment ("It is natural to...", "Many practitioners wonder...")
  2. Phenomenological inquiry ("Notice the felt sense...", "Observe the silent gap...")
  3. Precise Pāli gloss with English translation in parentheses
  4. Lineage simile & actionable application ("It is like a...", "Practice by...")
- Target **120–250 words** per assistant answer.
- Start user questions with "Ajahn, ..." format.

**Key constraint**: The QA pairs are generated programmatically as Python string literals (not by calling an LLM API). The agent writing this script must compose the QA content directly in the Python source code, using the chapter text as grounding reference.

### 3.2 — Run the gap filler

**Command**: `python fill_gaps.py`

---

## TASK 4: Create New Datasets for `[MISSING QA]` Books

The following 20 books with > 10,000 source words currently have **no dataset at all**. Create new `.jsonl` datasets for each.

### 4.1 — Books Requiring New Datasets

| # | Book Title | Source Words | Dir Name | Target Dataset File |
|---|---|---|---|---|
| 1 | An Introduction to the Life and Teachings of Ajahn Chah | 11,974 | `An Introduction to the Life and Teachings of Ajahn Chah - Ajahn Amaro` | `Intro_Life_Teachings_Ajahn_Chah_qa.jsonl` |
| 2 | CatApo Web | 44,165 | `CatApo Web - Thai Forest Tradition` | `CatApo_qa.jsonl` |
| 3 | Fear and Fearlessness Web | 13,889 | `Fear and Fearlessness Web - Thai Forest Tradition` | `Fear_and_Fearlessness_qa.jsonl` |
| 4 | HEA 1 Reality Web | 26,758 | `HEA 1 Reality Web - Thai Forest Tradition` | `HEA_1_Reality_qa.jsonl` |
| 5 | HEA 2 Emotion Web | 30,444 | `HEA 2 Emotion Web - Thai Forest Tradition` | `HEA_2_Emotion_qa.jsonl` |
| 6 | HEA 3 People Web | 24,265 | `HEA 3 People Web - Thai Forest Tradition` | `HEA_3_People_qa.jsonl` |
| 7 | HEA 4 Money Web | 19,493 | `HEA 4 Money Web - Thai Forest Tradition` | `HEA_4_Money_qa.jsonl` |
| 8 | HEA 5 Beyond Web | 33,887 | `HEA 5 Beyond Web - Thai Forest Tradition` | `HEA_5_Beyond_qa.jsonl` |
| 9 | HEA Anthology Web | 135,407 | `HEA Anthology Web - Thai Forest Tradition` | *Skip — covered by HEA 1-5 individual datasets* |
| 10 | Just One More | 12,954 | `Just One More - Ajahn Amaro` | `Just_One_More_qa.jsonl` |
| 11 | Bio.pdf (Less Is More) | 10,925 | `LessIsMore20Jan22 - Thai Forest Tradition` | `Less_Is_More_qa.jsonl` |
| 12 | Like a River | 16,927 | `Like a River - The life of a boy named Todd - Ajahn Pasanno` | `Like_a_River_qa.jsonl` |
| 13 | Mara Mangala web | 181,183 | `Mara Mangala web - Thai Forest Tradition` | *Skip — subset of Mara and the Mangala II* |
| 14 | Mara and the Mangala II | 160,268 | `Mara and the Mangala II Ajahn Amaro - Thai Forest Tradition` | `Mara_and_the_Mangala_II_qa.jsonl` |
| 15 | Mind Is What Matters NEW | 42,818 | `Mind Is What Matters NEW - Thai Forest Tradition` | `Mind_Is_What_Matters_qa.jsonl` |
| 16 | Rain on the Nile | 84,700 | `Rain on the Nile - Ajahn Amaro` | `Rain_on_the_Nile_qa.jsonl` |
| 17 | Roots Currents web | 85,815 | `Roots Currents web - Thai Forest Tradition` | `Roots_and_Currents_qa.jsonl` |
| 18 | Rugged Interdependency | 67,570 | `Rugged Interdependency - Ajahn Amaro` | `Rugged_Interdependency_qa.jsonl` |
| 19 | The Dhamma and the Real World | 11,610 | `The Dhamma and the Real World - Ajahn Pasanno and Ajahn Amaro` | `The_Dhamma_and_the_Real_World_qa.jsonl` |
| 20 | The Hush web | 12,366 | `The Hush web - Thai Forest Tradition` | `The_Hush_qa.jsonl` |

### 4.2 — Generation Strategy Per Book Size

| Source Words | Target QA Pairs |
|---|---|
| 10,000 – 20,000 | 15 pairs |
| 20,001 – 50,000 | 20 pairs |
| 50,001 – 100,000 | 30 pairs |
| 100,001+ | 40 pairs |

### 4.3 — For Each New Dataset

Create a Python generator script (e.g., `generate_missing_books_qa.py`) that:

1. **Reads** the source book's `full_book.txt` (first 2000 words) to understand the book's theme, author, and major topics.
2. **Reads** the source book's chapter list from `metadata.json`.
3. **Composes** the target number of QA pairs as Python string literal tuples `(question, answer)`.
4. **Each QA pair** must:
   - Be grounded in a specific chapter or theme from the source book
   - Follow the 4-part Thai Forest pedagogical structure
   - Use the exact standard system prompt
   - Target 120–250 words per answer
   - Start questions with "Ajahn, ..."
   - Include at least 1 Pāli term with English gloss per answer
   - Include at least 1 simile per answer (e.g., "It is like a...")
5. **Saves** each dataset to `datasets/<Target_Dataset_File>`.

### 4.4 — Update `corpus_summary.py` Custom Map

After creating new datasets, add entries to the `custom_map` dict in [`corpus_summary.py`](file:///c:/training-dhamma/dhamma/corpus_summary.py) (lines 122–177) for each new book→dataset mapping. For example:

```python
"CatApo Web": "CatApo_qa.jsonl",
"Fear and Fearlessness Web": "Fear_and_Fearlessness_qa.jsonl",
"HEA 1 Reality Web": "HEA_1_Reality_qa.jsonl",
# ... etc
```

---

## TASK 5: Deduplication & Quality Audit

### 5.1 — Run Deduplication Check

**Command**: `python check_duplicates.py`
**Working directory**: `c:\training-dhamma\dhamma`
**Expected result**: 0 intra-file exact duplicates, 0 inter-file exact duplicates.
**If duplicates found**: Rename the duplicate question text to make it unique (change a few words), then re-save the affected `.jsonl` file.

### 5.2 — Run Pedagogical Structure Audit

**Command**: `python audit_structure.py`
**Working directory**: `c:\training-dhamma\dhamma`
**Expected result**: All datasets show scores. Review any datasets marked with `(!)` (score < 45).

### 5.3 — Run Schema Verification

**Command**: `python verify_dataset.py datasets/<filename>.jsonl` for each new dataset.
Or use the merge script which verifies automatically (see Task 6).

---

## TASK 6: Rebuild Master Splits & Exports

### 6.1 — Rebuild Master + Train/Val Splits

**Command**: `python merge_and_split_dataset.py --val-ratio 0.1 --output-dir datasets/splits`
**Working directory**: `c:\training-dhamma\dhamma`

**Expected output**:
- `datasets/splits/master_dhamma_qa.jsonl` — all unique records merged
- `datasets/splits/train.jsonl` — 90% split
- `datasets/splits/val.jsonl` — 10% split
- Automatic verification of both splits prints `[PASSED]`

### 6.2 — Export ShareGPT Format

**Command**: `python export_formats.py --all-splits -f sharegpt`
**Working directory**: `c:\training-dhamma\dhamma`

**Expected output**:
- `datasets/exports/master_dhamma_qa_sharegpt.json`
- `datasets/exports/train_sharegpt.json`
- `datasets/exports/val_sharegpt.json`

---

## TASK 7: Re-Run Coverage Validation (Verification Pass)

**Command**: `python validate_coverage.py`
**Working directory**: `c:\training-dhamma\dhamma`

Verify that:
- All previously uncovered chapters now have matching QA pairs
- All previously missing Pāli terms now appear in at least one QA pair
- All previously `[MISSING QA]` books now have datasets
- Overall corpus chapter coverage is > 70%

---

## TASK 8: Commit & Push

### 8.1 — Stage All Changes

**Command**: `git add .`
**Working directory**: `c:\training-dhamma\dhamma`

### 8.2 — Commit

**Command**: `git commit -m "feat: independent validation + gap-fill — comprehensive chapter & concept coverage across all 60+ datasets"`

### 8.3 — Push

**Command**: `git push origin main`

---

## TASK 9: Update Walkthrough

Update `c:\training-dhamma\dhamma\WALKTHROUGH.md` with:
- Final dataset count
- Final QA pair count (train + val)
- Coverage validation results summary
- List of newly created datasets
