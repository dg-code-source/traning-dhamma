#!/usr/bin/env python3
"""
clean_datasets.py — Intra-dataset Deduplication and Quality Cleanup

Cleans intra-file duplicates across all datasets/*.jsonl files, keeping the richest
and highest-quality entry whenever duplicate questions are encountered.
"""

import os
import glob
import json
import re
import unicodedata
from typing import Dict, List, Tuple


def normalize_question(q: str) -> str:
    q = q.lower()
    q = unicodedata.normalize('NFKD', q).encode('ASCII', 'ignore').decode('utf-8')
    q = re.sub(r"[^\w\s]", " ", q)
    q = re.sub(r"\s+", " ", q).strip()
    return q


def clean_file(file_path: str) -> Tuple[int, int]:
    with open(file_path, "r", encoding="utf-8-sig") as f:
        lines = [line.strip() for line in f if line.strip()]

    original_count = len(lines)
    seen_map = {}
    cleaned_records = []

    for line in lines:
        try:
            rec = json.loads(line)
        except Exception:
            continue

        q = rec["messages"][1]["content"].strip()
        ans = rec["messages"][2]["content"].strip()
        norm_q = normalize_question(q)
        ans_word_count = len(ans.split())

        if norm_q not in seen_map:
            seen_map[norm_q] = (rec, ans_word_count)
            cleaned_records.append(rec)
        else:
            # If current record is longer / more substantive than previously seen version, update it
            prev_rec, prev_count = seen_map[norm_q]
            if ans_word_count > prev_count:
                for idx, r in enumerate(cleaned_records):
                    if normalize_question(r["messages"][1]["content"]) == norm_q:
                        cleaned_records[idx] = rec
                        seen_map[norm_q] = (rec, ans_word_count)
                        break

    # Save cleaned file
    with open(file_path, "w", encoding="utf-8") as f:
        for r in cleaned_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    return original_count, len(cleaned_records)


def main():
    files = sorted(glob.glob("datasets/*.jsonl"))
    total_orig = 0
    total_cleaned = 0

    print(f"Cleaning intra-file duplicates across {len(files)} files...")
    for fpath in files:
        orig, clean = clean_file(fpath)
        total_orig += orig
        total_cleaned += clean
        if orig != clean:
            print(f"  • {os.path.basename(fpath)}: {orig} -> {clean} (removed {orig - clean} duplicates)")

    print(f"\nDone! Total records before: {total_orig}, after cleaning: {total_cleaned} (removed {total_orig - total_cleaned} duplicates)")


if __name__ == "__main__":
    main()
