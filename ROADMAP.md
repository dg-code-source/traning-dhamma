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

| # | Feature                            | Effort    | Impact | LLM Cost | Status |
|---|------------------------------------|-----------|--------|----------|--------|
| 1 | Near-duplicate semantic detector   | Medium    | High   | Zero     | [ ]    |
| 2 | 4-part structural compliance check | Low       | High   | Zero     | [ ]    |
| 3 | Pāli term coverage report          | Low       | Medium | Zero     | [ ]    |
| 4 | Token length distribution          | Low       | Medium | Zero     | [ ]    |
| 5 | Question paraphrase augmentation   | Medium    | Medium | Zero     | [ ]    |
| 6 | Multi-turn conversation converter  | Medium    | Medium | Zero     | [ ]    |
| 7 | DPO preference pairs generator     | High      | High   | High     | [ ]    |
| 8 | Git pre-commit hook                | Very Low  | Medium | Zero     | [ ]    |
| 9 | Batch EPUB/PDF processor           | Low       | Low    | Zero     | [ ]    |
|10 | Hugging Face Hub uploader          | Low       | Medium | Zero     | [ ]    |
|11 | Training config generator          | Low       | Medium | Zero     | [ ]    |

---

## Budget-Aware Build Order

> **Context**: LLM tokens are a scarce resource. The order of work must maximize
> protection of existing investment before spending tokens on new generation.
> 10 of the 11 features cost zero LLM tokens — build those first.

### Phase 1 — Protect and Audit (Zero LLM Cost)

Build these before generating a single new QA pair. They audit what you already have
and tell you exactly where the gaps are, so no future token is wasted on guesswork.

| Step | Feature | Why first |
|---|---|---|
| 1 | **#2 `audit_structure.py`** | Reveals which existing answers are structurally weak before you decide what to regenerate |
| 2 | **#1 `check_duplicates.py`** | Reveals which topics are already saturated so you don't cover the same ground twice |
| 3 | **#3 `pali_coverage.py`** | Gives a precise list of untaught Pāli concepts — turns guesswork into targeted generation |
| 4 | **#8 Git pre-commit hook** | One-time setup; prevents malformed records from slipping in and requiring costly fixes later |

### Phase 2 — Multiply Existing Pairs (Zero LLM Cost)

You have 571 high-quality pairs representing significant token investment.
These features multiply that value at zero additional token cost.

| Step | Feature | Multiplier effect |
|---|---|---|
| 5 | **#5 `augment_dataset.py`** | Rule-based question rephrasing: 571 pairs → ~1,400 training records, no LLM calls |
| 6 | **#6 `make_multiturn.py`** | Restructure related pair clusters into 2-turn dialogues; zero LLM calls |

### Phase 3 — Infrastructure (Zero LLM Cost, Do When Ready to Train)

| Step | Feature | When |
|---|---|---|
| 7 | **#4 Token distribution** | Before first training run — catch truncation risks |
| 8 | **#10 HF Hub uploader** | When ready to push to Hugging Face for training |
| 9 | **#11 Training config generator** | Immediately before first training run |
| 10 | **#9 Batch extractor** | When adding many new source books at once |

### Phase 4 — Defer Until Token Budget Opens

These require LLM calls to generate new content. Only begin after Phase 1 has
identified specific, targeted gaps — so every token spent fills a real need.

| Step | Feature | Token cost |
|---|---|---|
| 11 | **New source QA generation** | High — only for gaps identified by `pali_coverage.py` and `audit_structure.py` |
| 12 | **#7 DPO pair generation** | High — generates "rejected" answers via LLM; highest ROI for alignment quality |

---

## Guiding Principle

> *Quality is paramount. Do not force-fit.* Every enhancement must serve authentic,
> deeply grounded Dhamma instruction. Augmented and generated pairs must be reviewed
> for doctrinal accuracy before merging into training data.
>
> *Spend tokens on gaps, not on ground already covered.*
