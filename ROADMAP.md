# Future Functionality Roadmap — Dhamma Training Pipeline

*Written: 2026-08-23*

This document tracks planned enhancements to the pipeline, grouped by priority and effort.
Current corpus state at time of writing: **571 records, 12 datasets**.

---

## 🔴 High Value — Directly Improves Quality

### 1. Near-Duplicate Semantic Detector
**File**: `check_duplicates.py`
**Problem**: `merge_and_split_dataset.py` only removes *exact* string duplicates. Semantically similar questions like *"How do I work with anger?"* and *"What should I do when anger arises in meditation?"* both pass through, diluting training signal.
**Approach**: Compute TF-IDF or sentence-embedding cosine similarity across all user questions. Flag pairs above a configurable threshold (e.g., 0.85) for human review rather than auto-deleting.
**Usage**:
```bash
python check_duplicates.py --threshold 0.85
python check_duplicates.py --threshold 0.85 --report duplicates_report.txt
```
**Output**: Report listing flagged near-duplicate pairs with similarity score, source file, and both questions side-by-side.

---

### 2. Structural Compliance Checker (4-Part Answer Audit)
**File**: `audit_structure.py` (or add `--deep` flag to `verify_dataset.py`)
**Problem**: `verify_dataset.py` checks *schema* but not *pedagogical quality*. An answer can pass schema validation while being generic, Pāli-free, and simile-free.
**Checks**:
- Does the answer contain at least one Pāli term?
- Is there a parenthetical gloss (e.g., `(taṇhā)`)?
- Is there a concrete simile or metaphor?
- Is the answer under 50 words (too brief) or over 300 words (padded)?

**Usage**:
```bash
python audit_structure.py datasets/In_Simple_Terms_Similes_qa.jsonl
python audit_structure.py --all-datasets
```

---

### 3. Pāli Term Coverage Report
**File**: Add section to `corpus_summary.py` or standalone `pali_coverage.py`
**Problem**: No visibility into which Pāli concepts are taught frequently vs. absent.
**Approach**: Scan all assistant answers for a curated list of ~60 Pāli terms. Produce a frequency table sorted by usage count, flagging underrepresented or missing terms.

---

## 🟡 Medium Value — Training and Data Health

### 4. Token Length Distribution Analyzer
**File**: Add `--token-stats` flag to `corpus_summary.py`
**Approach**: Use `tiktoken` to measure total token count per record. Output min/max/p50/p95/p99 per dataset; flag records exceeding a configurable limit (default: 512 tokens).

---

### 5. Question Paraphrase Augmentation
**File**: `augment_dataset.py`
**Problem**: Datasets with fewer than 20 pairs are underweighted in training. The model learns exact phrasing but not variants.
**Approach**: For each user question, generate 2-3 paraphrase variants with the same assistant answer. Store in `datasets/augmented/` — never mixed into primary QA files.

```bash
python augment_dataset.py datasets/Daughters_and_Sons_qa.jsonl --variants 2
```

---

### 6. Multi-Turn Conversation Converter
**File**: `make_multiturn.py`
**Problem**: Current dataset is 100% single-turn. Real Dhamma dialogue involves follow-up questions and deepening inquiry.
**Approach**: Construct 2-3 turn conversations from related QA pairs in the same thematic cluster, formatted as a single `messages` array with alternating user/assistant turns.

---

### 7. DPO / Preference Pairs Generator
**File**: `generate_dpo_pairs.py`
**Problem**: Standard SFT trains the model to imitate. DPO additionally trains it to prefer good answers over bad ones — more robust alignment.
**Approach**: For each existing QA pair (the "chosen" answer), generate a degraded "rejected" version by removing the Pāli gloss, the simile, and shortening to a generic 2-sentence response.
**Output**: `datasets/dpo/dpo_pairs.jsonl` in standard DPO format:
```json
{"prompt": "...", "chosen": "...full 4-part answer...", "rejected": "...generic response..."}
```

---

## 🟢 Lower Effort — Pipeline Polish

### 8. Git Pre-Commit Hook
**File**: `.git/hooks/pre-commit` (setup: `setup_hooks.py`)
**What it does**: Auto-runs `verify_dataset.py` on any staged `.jsonl` file before allowing a commit. Blocks the commit if validation fails.

```bash
python setup_hooks.py
```

---

### 9. Batch EPUB/PDF Processor
**File**: `batch_extract.py`
**What it does**: Scans a directory for any `.epub` or `.pdf` files not yet extracted and processes them all in sequence.

```bash
python batch_extract.py documents/raw_epubs/
```

---

### 10. Hugging Face Hub Uploader
**File**: `upload_to_hub.py`
**What it does**: Pushes `train.jsonl` and `val.jsonl` directly to a private HF repository. Eliminates the manual upload step before training with Unsloth or Axolotl.

```bash
python upload_to_hub.py --repo your-username/dhamma-training --private
```

---

### 11. Training Config Generator
**File**: `generate_train_config.py`
**What it does**: Reads corpus stats and outputs a ready-to-use config for Axolotl, LLaMA-Factory, or Unsloth.

```bash
python generate_train_config.py --framework axolotl --output configs/axolotl_config.yaml
```

---

## Implementation Priority

| # | Feature                            | Effort    | Impact | Status |
|---|------------------------------------|-----------|--------|--------|
| 1 | Near-duplicate semantic detector   | Medium    | High   | [ ]    |
| 2 | 4-part structural compliance check | Low       | High   | [ ]    |
| 3 | Pāli term coverage report          | Low       | Medium | [ ]    |
| 4 | Token length distribution          | Low       | Medium | [ ]    |
| 5 | Question paraphrase augmentation   | Medium    | Medium | [ ]    |
| 6 | Multi-turn conversation converter  | Medium    | Medium | [ ]    |
| 7 | DPO preference pairs generator     | High      | High   | [ ]    |
| 8 | Git pre-commit hook                | Very Low  | Medium | [ ]    |
| 9 | Batch EPUB/PDF processor           | Low       | Low    | [ ]    |
|10 | Hugging Face Hub uploader          | Low       | Medium | [ ]    |
|11 | Training config generator          | Low       | Medium | [ ]    |

---

## Guiding Principle

> *Quality is paramount. Do not force-fit.* Every enhancement must serve authentic,
> deeply grounded Dhamma instruction. Augmented and generated pairs must be reviewed
> for doctrinal accuracy before merging into training data.
