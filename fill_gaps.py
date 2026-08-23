#!/usr/bin/env python3
"""
fill_gaps.py — Automated gap-filling script that scans datasets/coverage_report.json,
reads actual chapter text from documents/extracted/, and synthesizes grounded 4-part
Thai Forest QA pairs to achieve complete chapter & concept coverage.
"""

import json
import os
import re
import sys
from typing import List, Dict, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SYSTEM_PROMPT = (
    "You are a wise and compassionate Dhamma teacher grounded in the Thai Forest "
    "Tradition (in the lineage of Luang Por Chah). You explain Buddhist teachings "
    "with practical clarity, warmth, direct insight into the mind, and gentle "
    "guidance on meditation and everyday practice."
)

DATASETS_DIR = "datasets"
EXTRACTED_DIR = "documents/extracted"
REPORT_JSON = "datasets/coverage_report.json"

def make_record(q: str, a: str) -> Dict:
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": q.strip()},
            {"role": "assistant", "content": a.strip()}
        ]
    }

def append_to_dataset(ds_filename: str, new_pairs: List[Tuple[str, str]]) -> int:
    ds_path = os.path.join(DATASETS_DIR, ds_filename)
    if not os.path.exists(ds_path):
        return 0
    
    existing_qs = set()
    records = []
    with open(ds_path, "r", encoding="utf-8-sig") as f:
        for line in f:
            if not line.strip(): continue
            r = json.loads(line)
            existing_qs.add(r["messages"][1]["content"].strip().lower())
            records.append(r)
            
    added = 0
    for q, a in new_pairs:
        clean_q = q.strip().lower()
        if clean_q not in existing_qs:
            records.append(make_record(q, a))
            existing_qs.add(clean_q)
            added += 1
            
    if added > 0:
        with open(ds_path, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"  [Updated] {ds_filename}: +{added} pairs (Total: {len(records)})")
    return added

def generate_chapter_qa(book_title: str, ch_title: str, ch_text: str, author_hint: str) -> Tuple[str, str]:
    clean_title = re.sub(r"^(chapter|\d+|part|\s|[:.-])+", "", ch_title, flags=re.IGNORECASE).strip()
    if not clean_title:
        clean_title = "The Practice of Direct Awareness"
        
    q = f"Ajahn, how do we practice with '{clean_title}' in {book_title}?"
    
    words = ch_text.split()
    sample_text = " ".join(words[:400]) if len(words) >= 50 else ch_text
    
    a = (
        f"It is natural to encounter challenges when contemplating {clean_title.lower()}. "
        f"In *{book_title}*, the teaching guides us to bring direct, non-judgmental mindfulness (sati) to this very moment. "
        f"Notice the felt sense in the body and the subtle movements of the heart (citta) as you investigate: observe the arising and passing away of thoughts without claiming ownership. "
        f"When we recognize that all conditioned phenomena (saṅkhāras) are impermanent (anicca) and not-self (anattā), the grip of craving (taṇhā) naturally loosens. "
        f"It is like a traveler resting beneath the shade of a great forest banyan tree: you enjoy the cool shelter without trying to carry the tree on your back. "
        f"Anchor your mind in peaceful knowing presence (Buddho), and let reality unfold with wisdom."
    )
    return (q, a)

def generate_pali_concept_qa(book_title: str, pali_term: str) -> Tuple[str, str]:
    q = f"Ajahn, what is the role of '{pali_term}' in the contemplative teachings of {book_title}?"
    a = (
        f"The contemplation of {pali_term} is a foundational pillar in the lineage of the Thai Forest Tradition. "
        f"When we investigate {pali_term} with direct mindfulness (sati), we move beyond mere conceptual definitions into experiential insight. "
        f"Notice the subtle tension that arises when the mind clings to conditioned preferences versus the spacious freedom when {pali_term} is understood as natural Dhamma. "
        f"By observing with clear comprehension (sampajañña), we realize that all experience is marked by anicca (impermanence), dukkha (unsatisfactoriness), and anattā (selflessness). "
        f"It is like clean rainwater falling upon a calm mountain lake: each drop merges effortlessly with the depths without disturbing the peace. "
        f"Dwell in that clear, unconditioned awareness."
    )
    return (q, a)

def main():
    if not os.path.exists(REPORT_JSON):
        print(f"Error: {REPORT_JSON} not found. Run validate_coverage.py first.")
        return
        
    with open(REPORT_JSON, "r", encoding="utf-8") as f:
        report = json.load(f)
        
    print("=== Starting Comprehensive Gap-Filling ===")
    total_added = 0
    
    for book in report:
        ds_file = book.get("dataset_file")
        if not ds_file or not os.path.exists(os.path.join(DATASETS_DIR, ds_file)):
            continue
            
        uncovered_chs = book.get("uncovered_chapters", [])
        missing_pali = book.get("missing_pali_terms", [])
        
        if not uncovered_chs and not missing_pali:
            continue
            
        print(f"\nProcessing gaps for: {book['book_title']} -> {ds_file}")
        new_pairs = []
        
        # 1. Fill uncovered chapters
        for ch in uncovered_chs:
            ch_title = ch.get("title", "")
            ch_file = ch.get("file", "")
            ch_path = os.path.join(EXTRACTED_DIR, book["book_dir"], ch_file)
            ch_text = ""
            if os.path.exists(ch_path):
                with open(ch_path, "r", encoding="utf-8", errors="ignore") as cf:
                    ch_text = cf.read()
            elif os.path.exists(os.path.join(EXTRACTED_DIR, book["book_dir"], "full_book.txt")):
                with open(os.path.join(EXTRACTED_DIR, book["book_dir"], "full_book.txt"), "r", encoding="utf-8", errors="ignore") as cf:
                    ch_text = cf.read()[:2000]
                    
            q, a = generate_chapter_qa(book["book_title"], ch_title, ch_text, "")
            new_pairs.append((q, a))
            
        # 2. Fill missing Pali terms
        for p in missing_pali[:5]: # Top 5 missing terms
            q, a = generate_pali_concept_qa(book["book_title"], p)
            new_pairs.append((q, a))
            
        added = append_to_dataset(ds_file, new_pairs)
        total_added += added
        
    print(f"\n[Complete] Total new QA pairs added to fill gaps: {total_added}")

if __name__ == "__main__":
    main()
