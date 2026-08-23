#!/usr/bin/env python3
"""
check_duplicates.py — Semantic & Exact Duplicate Detector for Dhamma Datasets

Identifies exact duplicates and near-duplicate questions across all .jsonl dataset files
using character/word n-gram Jaccard and normalized similarity.

Usage:
  python check_duplicates.py
  python check_duplicates.py --threshold 0.80
  python check_duplicates.py --report duplicates_report.txt
"""

import sys
import os
import glob
import json
import argparse
import re
import unicodedata
from collections import defaultdict
from typing import List, Dict, Tuple, Set

# Ensure stdout supports UTF-8 on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def normalize_text(text: str) -> str:
    """Normalizes text for robust semantic comparison."""
    # Lowercase & strip diacritics
    text = text.lower()
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
    # Replace punctuation with spaces
    text = re.sub(r"[^\w\s]", " ", text)
    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


def get_ngrams(text: str, n: int = 3) -> Set[str]:
    """Extract character n-grams."""
    if len(text) < n:
        return {text}
    return {text[i:i+n] for i in range(len(text) - n + 1)}


def jaccard_similarity(set1: Set[str], set2: Set[str]) -> float:
    """Compute Jaccard similarity between two sets."""
    if not set1 or not set2:
        return 0.0
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union if union > 0 else 0.0


def main():
    parser = argparse.ArgumentParser(description="Check for exact and near-duplicate questions across datasets.")
    parser.add_argument("--threshold", type=float, default=0.85, help="Similarity threshold for near-duplicates (0.0 to 1.0, default: 0.85)")
    parser.add_argument("--report", type=str, default=None, help="Optional output path for detailed report text file")
    parser.add_argument("--datasets-dir", type=str, default="datasets", help="Directory containing .jsonl dataset files")
    args = parser.parse_args()

    files = sorted(glob.glob(os.path.join(args.datasets_dir, "*.jsonl")))
    if not files:
        print(f"No .jsonl dataset files found in {args.datasets_dir}")
        return

    records = []  # (filename, line_num, original_q, norm_q, ngrams)
    exact_map = defaultdict(list)

    print(f"Scanning {len(files)} dataset files...")
    for fpath in files:
        fname = os.path.basename(fpath)
        with open(fpath, "r", encoding="utf-8-sig") as f:
            for line_idx, line in enumerate(f, start=1):
                line_str = line.strip()
                if not line_str:
                    continue
                try:
                    data = json.loads(line_str)
                    q = data["messages"][1]["content"].strip()
                    norm_q = normalize_text(q)
                    ngrams = get_ngrams(norm_q, n=3)
                    entry = {
                        "file": fname,
                        "line": line_idx,
                        "question": q,
                        "norm_q": norm_q,
                        "ngrams": ngrams
                    }
                    records.append(entry)
                    exact_map[norm_q].append(entry)
                except Exception:
                    continue

    print(f"Loaded {len(records)} total records.")

    # 1. Exact duplicates
    exact_dupes = {k: v for k, v in exact_map.items() if len(v) > 1}
    intra_exact = []
    inter_exact = []

    for norm_q, entries in exact_dupes.items():
        files_involved = {e["file"] for e in entries}
        if len(files_involved) == 1:
            intra_exact.append((norm_q, entries))
        else:
            inter_exact.append((norm_q, entries))

    # 2. Near duplicates (above threshold) with fast length pruning
    near_dupes = []
    num_recs = len(records)
    thresh = args.threshold
    for i in range(num_recs):
        r1 = records[i]
        s1 = r1["ngrams"]
        len1 = len(s1)
        if len1 == 0:
            continue
        min_len = len1 * thresh
        max_len = len1 / thresh
        for j in range(i + 1, num_recs):
            r2 = records[j]
            # Skip if exact match (already captured)
            if r1["norm_q"] == r2["norm_q"]:
                continue
            s2 = r2["ngrams"]
            len2 = len(s2)
            if len2 < min_len or len2 > max_len:
                continue
            sim = jaccard_similarity(s1, s2)
            if sim >= thresh:
                near_dupes.append((sim, r1, r2))

    # Sort near dupes by similarity desc
    near_dupes.sort(key=lambda x: x[0], reverse=True)

    # Print summary
    print(f"\n{'='*80}")
    print(f"{'DUPLICATE QUESTION ANALYSIS REPORT':^80}")
    print(f"{'='*80}")
    print(f"Total Records Analyzed:           {len(records)}")
    print(f"Intra-file Exact Duplicates:       {len(intra_exact)} clusters ({sum(len(v) for _, v in intra_exact)} total rows)")
    print(f"Inter-file Exact Duplicates:       {len(inter_exact)} clusters ({sum(len(v) for _, v in inter_exact)} total rows)")
    print(f"Near-Duplicates (Sim >= {args.threshold:.2f}):      {len(near_dupes)} pairs")
    print(f"{'='*80}\n")

    if intra_exact:
        print("[!] INTRA-FILE EXACT DUPLICATES (Must be fixed):")
        for norm_q, entries in intra_exact:
            fname = entries[0]["file"]
            lines = [str(e["line"]) for e in entries]
            print(f"  • [{fname}] (Lines: {', '.join(lines)})")
            print(f"    Q: \"{entries[0]['question']}\"\n")

    if inter_exact:
        print("[!] INTER-FILE EXACT DUPLICATES (Cross-dataset overlap):")
        for norm_q, entries in inter_exact[:10]:
            print(f"  • Q: \"{entries[0]['question']}\"")
            for e in entries:
                print(f"    - {e['file']}: Line {e['line']}")
            print()
        if len(inter_exact) > 10:
            print(f"  ... and {len(inter_exact) - 10} more cross-file duplicates.\n")

    if near_dupes:
        print(f"[i] TOP NEAR-DUPLICATES (Similarity >= {args.threshold:.2f}):")
        for sim, r1, r2 in near_dupes[:10]:
            print(f"  • Sim: {sim:.2f}")
            print(f"    A ({r1['file']}:{r1['line']}): \"{r1['question']}\"")
            print(f"    B ({r2['file']}:{r2['line']}): \"{r2['question']}\"\n")

    # Optional report output file
    if args.report:
        with open(args.report, "w", encoding="utf-8") as rf:
            rf.write("=== DHAMMA DATASET DUPLICATE REPORT ===\n\n")
            rf.write(f"Total Records: {len(records)}\n")
            rf.write(f"Intra-file Exact Duplicates: {len(intra_exact)}\n")
            rf.write(f"Inter-file Exact Duplicates: {len(inter_exact)}\n")
            rf.write(f"Near-Duplicates (>= {args.threshold}): {len(near_dupes)}\n\n")

            rf.write("--- INTRA-FILE EXACT DUPLICATES ---\n")
            for norm_q, entries in intra_exact:
                rf.write(f"File: {entries[0]['file']}, Lines: {[e['line'] for e in entries]}\n")
                rf.write(f"Q: {entries[0]['question']}\n\n")

            rf.write("--- INTER-FILE EXACT DUPLICATES ---\n")
            for norm_q, entries in inter_exact:
                rf.write(f"Q: {entries[0]['question']}\n")
                for e in entries:
                    rf.write(f"  {e['file']}:{e['line']}\n")
                rf.write("\n")

            rf.write("--- NEAR DUPLICATES ---\n")
            for sim, r1, r2 in near_dupes:
                rf.write(f"Sim: {sim:.3f}\n")
                rf.write(f"  {r1['file']}:{r1['line']}: {r1['question']}\n")
                rf.write(f"  {r2['file']}:{r2['line']}: {r2['question']}\n\n")
        print(f"Detailed duplicate report saved to: {args.report}")


if __name__ == "__main__":
    main()
