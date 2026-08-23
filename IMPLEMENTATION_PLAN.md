# Independent Validation: Training Data vs Source Documents

## Goal

Perform a comprehensive, two-layer independent validation of all 50 training datasets against their 75 extracted source books. Identify every topic coverage gap (uncovered chapters and missing key concepts), auto-generate new QA pairs to fill all gaps, and rebuild the master corpus.

---

## User Decisions (from /grill-me)

| Decision | Choice |
|:---|:---|
| Primary concern | **Topic Coverage** — verify major themes/chapters are represented |
| Scope | **All 50 datasets** — comprehensive audit |
| Action on gaps | **Report + Auto-Fill** — generate QA pairs for gaps |
| Coverage metric | **Both layers** — chapter-level AND keyword/concept extraction |
| Auto-fill threshold | **Any gap at all** — fill every uncovered chapter/concept |

---

## Phase 1: Build `validate_coverage.py` (Automated Analysis Tool)

### Layer 1 — Chapter Coverage Analysis

For each source book → dataset mapping (from `corpus_summary.py` `custom_map` + fuzzy matching):

1. **Read** the source book's `metadata.json` to get the list of chapters with titles and word counts.
2. **Filter** out non-substantive chapters (e.g., "Copyright", "Acknowledgements", "Glossary", "Preface", "Contents", "Abbreviations", "Note to the reader", "Further resources", "About the author") — these don't need QA pairs.
3. **Read** all QA pairs from the corresponding dataset `.jsonl` file.
4. **For each substantive chapter**, fuzzy-match the chapter title keywords against the combined question + answer text of all QA pairs. A chapter is "covered" if any QA pair references its core topic with similarity ≥ 0.4 (lenient, since QA pairs may paraphrase chapter titles).
5. **Output** per-book: total substantive chapters, covered chapters, uncovered chapter titles, coverage percentage.

### Layer 2 — Keyword/Concept Coverage Analysis

For each source book:

1. **Read** the source book's `full_book.txt`.
2. **Extract key Pāli terms** by scanning for known Pāli vocabulary from a curated list (e.g., *anicca, dukkha, anattā, taṇhā, sati, samādhi, paññā, sīla, mettā, karuṇā, muditā, upekkhā, nibbāna, saṅkhāra, vipassanā, jhāna, kamma, bhāvanā, papañca, suññatā, pīti, sukha, vedanā, saṃsāra, paṭicca-samuppāda, cetanā, avijjā, lobha, dosa, moha, khanti, nekkhamma, adhiṭṭhāna, viriya, sacca, ānapānasati, brahmavihāra, kilesa*) — count occurrences per term in the source text.
3. **Extract thematic keywords** by identifying the top 15–20 most frequent multi-word noun phrases and distinctive terms from the source text (excluding common English stop words).
4. **Check** whether each significant Pāli term (appearing ≥ 3 times in source) and each top thematic keyword appears in at least one QA pair in the dataset.
5. **Output** per-book: Pāli terms found in source but missing from QA, thematic keywords found in source but missing from QA.

### Output Format

The tool will produce:
- A **per-book JSON report** saved to `datasets/coverage_report.json`
- A **human-readable markdown artifact** (`coverage_report.md`) with tables showing:
  - Book title, total chapters, covered chapters, coverage %, uncovered chapter titles
  - Missing Pāli terms and thematic keywords per book
  - Overall corpus-wide coverage statistics

---

## Phase 2: Run Analysis Across All 50 Datasets

Execute `python validate_coverage.py` to produce the full gap report.

### Expected Challenges

| Challenge | Mitigation |
|:---|:---|
| Some books have 100+ fragmented chapters (e.g., The Island with 364 chapters) | Filter by word count ≥ 200 words; merge fragments with identical base titles |
| Some extracted books have garbled/generic chapter titles ("Blank Page", "Island", "BE...") | Skip chapters with titles < 3 meaningful words or matching known junk patterns |
| YouTube transcript sources have no chapter structure | Skip chapter analysis for transcript-only sources; run keyword analysis only |
| Some books map to the same dataset (e.g., "Its Like This Web" and "It's Like This 108 Dhamma Similes") | Merge chapter lists when multiple source books map to the same dataset |

---

## Phase 3: Auto-Generate Gap-Filling QA Pairs

For every uncovered chapter and missing concept identified in Phase 2:

1. **Read** the source chapter text (e.g., `chapter_05_5. Immanent and Transcendent.txt`).
2. **Generate** 1–3 high-quality QA pairs per uncovered chapter, grounded in the actual chapter content. Each pair must follow the 4-part Thai Forest pedagogical structure:
   - Empathetic Acknowledgment
   - Phenomenological Observation / Direct Inquiry
   - Precise Pāli glosses
   - Lineage simile & actionable application
3. **Generate** 1 QA pair per missing key Pāli concept, tying it to content specific to that source book.
4. **Append** new pairs to the existing dataset files (not overwrite).
5. **Use the standard system prompt** exactly as defined in `RULES.md`.

### Generation Strategy

- For books with extracted chapter text: **read the actual chapter** and create QA pairs that are grounded in its specific teachings, terminology, and examples.
- For anthology/compendium books (HEA, CatApo, Mara Mangala, etc.) that currently have `[MISSING QA]`: create new datasets with 15–25 pairs each.
- Target answer length: **120–250 words** per answer.

---

## Phase 4: Validation & Deduplication

After gap-filling:

1. **Run** `python check_duplicates.py` — ensure 0 exact duplicates and review near-duplicates.
2. **Run** `python audit_structure.py` — verify all datasets maintain pedagogical quality.
3. **Run** `python verify_dataset.py` on all datasets — ensure 100% schema compliance.
4. **Fix** any issues found (rename duplicate questions, adjust word counts, etc.).

---

## Phase 5: Rebuild Master Splits & Exports

1. **Run** `python merge_and_split_dataset.py --val-ratio 0.1 --output-dir datasets/splits`
2. **Run** `python export_formats.py --all-splits -f sharegpt`
3. **Update** `corpus_summary.py` `custom_map` if new datasets were created for previously `[MISSING QA]` books.

---

## Phase 6: Commit & Push

```bash
git add .
git commit -m "feat: independent validation + gap-fill — comprehensive chapter & concept coverage across all 50+ datasets"
git push origin main
```

---

## Verification Checklist

- [ ] `validate_coverage.py` produces accurate chapter-to-QA mapping for all 50 datasets
- [ ] Coverage report artifact shows per-book stats with uncovered chapters and missing concepts
- [ ] Gap-filling QA pairs are grounded in actual source chapter text
- [ ] All new pairs follow 4-part Thai Forest pedagogical structure
- [ ] 0 exact duplicate questions across the entire corpus
- [ ] 100% schema compliance across all datasets
- [ ] Master splits rebuilt and exported
- [ ] Changes committed and pushed

---

## Open Questions

> **Books with `[MISSING QA]`**: There are ~20 extracted books that currently have no dataset at all (e.g., HEA Anthology, Rain on the Nile, Rugged Interdependency, Mara Mangala, CatApo, etc.). Create new datasets only for books with **> 10,000 words** of source content, as smaller extracts may not warrant standalone datasets.
