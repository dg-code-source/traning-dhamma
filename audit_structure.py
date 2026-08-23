#!/usr/bin/env python3
"""
audit_structure.py — Automated Pedagogical & Structural Compliance Auditor

Audits Dhamma Chat SFT datasets against the 4-part Thai Forest pedagogical standard:
1. Empathetic Acknowledgment (warmly meeting practitioner's experience)
2. Core Dhamma Insight & Phenomenological Observation (direct internal inquiry)
3. Precise Pāli Terminology with immediate gloss
4. Concrete Practice Application & Lineage Similes

Usage:
  python audit_structure.py datasets/In_Simple_Terms_Similes_qa.jsonl
  python audit_structure.py --all-datasets
  python audit_structure.py --all-datasets --verbose
"""

import sys
import os
import glob
import json
import argparse
import re
from typing import Dict, List, Tuple, Any

# Ensure stdout supports UTF-8 on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Canonical system prompt from RULES.md
REQUIRED_SYSTEM_PROMPT = (
    "You are a wise and compassionate Dhamma teacher grounded in the Thai Forest "
    "Tradition (in the lineage of Luang Por Chah). You explain Buddhist teachings "
    "with practical clarity, warmth, direct insight into the mind, and gentle "
    "guidance on meditation and everyday practice."
)

PALI_TERMS = [
    "dukkha", "anicca", "anatta", "anattā", "sati", "samādhi", "samadhi",
    "paññā", "panna", "pañña", "kamma", "karma", "taṇhā", "tanha",
    "nibbāna", "nibbana", "kilesa", "saṅkhāra", "sankhara", "buddho",
    "dhamma", "vinaya", "sīla", "sila", "jhāna", "jhana", "upādāna", "upadana",
    "bhāvanā", "bhavana", "papañca", "papanca", "avijjā", "avijja", "māna", "mana",
    "mettā", "metta", "karuṇā", "karuna", "muditā", "mudita", "upekkhā", "upekkha",
    "avippaṭisāra", "avippatisara", "yoniso manasikāra", "yoniso manasikara",
    "khandha", "khandhas", "vedanā", "vedana", "saññā", "sanna", "citta",
    "samatha", "vipassanā", "vipassana", "viriya", "hiri", "ottappa",
    "magga", "phala", "ariya", "saṅgha", "sangha", "asubha", "maranasati",
    "maraṇasati", "samudaya", "nirodha", "appamāda", "appamada", "tudong", "dhutaṅga"
]

SIMILE_PATTERNS = [
    r"\blike\s+(?:a|an|the)\b",
    r"\bsimilar\s+to\b",
    r"\bas\s+if\b",
    r"\bjust\s+as\b",
    r"\banalogy\b",
    r"\bsimile\b",
    r"\bmetaphor\b",
    r"\bit(?:'s|\s+is)\s+like\b",
    r"\bpicture\s+(?:a|this)\b",
    r"\bholding\s+(?:a\s+)?hot\s+coal\b",
    r"\bhub\s+of\s+the\s+wheel\b",
    r"\brock\s+tumbler\b",
    r"\bcobra\b",
    r"\bstill(?:,\s*|\s+)flowing\s+water\b",
    r"\bopen\s+palm\b",
    r"\bcup\s+of\s+water\b",
    r"\bdirty\s+cloth\b",
    r"\btree\b",
    r"\bforest\b",
    r"\bmirror\b"
]

EMPATHY_PATTERNS = [
    r"\bit\s+is\s+(?:very\s+)?(?:natural|common|understandable|normal)\b",
    r"\bmany\s+(?:sincere\s+)?practitioners\b",
    r"\bwhen\s+(?:we|you)\s+(?:encounter|experience|feel|struggle|notice|face)\b",
    r"\bdo\s+not\s+(?:be\s+discouraged|worry|despair|blame)\b",
    r"\bwith\s+warmth\b",
    r"\bgently\b",
    r"\bmeet\s+(?:this|the|your)\b",
    r"\bwelcome\s+(?:the|this)\b",
    r"\bheart\b",
    r"\bcompassion\b",
    r"\bkindness\b",
    r"\backnowledge\b",
    r"\bpatience\b"
]

PHENOMENOLOGICAL_PATTERNS = [
    r"\bnotice\b",
    r"\bobserve\b",
    r"\bfelt\s+sense\b",
    r"\bphysical\s+(?:sensation|tension|feeling|tightness|pressure)\b",
    r"\bsilent\s+(?:gap|space|presence|awareness)\b",
    r"\bdirect\s+(?:experience|observation|insight|awareness)\b",
    r"\barising\s+and\s+(?:ceasing|passing)\b",
    r"\bknowing\b",
    r"\bwatcher\b",
    r"\binvestigate\b",
    r"\bbody\b",
    r"\bbreath\b",
    r"\bchest\b",
    r"\bthroat\b",
    r"\bstomach\b",
    r"\bfeeling\s+in\s+the\b"
]


def audit_record(record: Dict[str, Any], line_num: int) -> Tuple[bool, List[str], Dict[str, Any]]:
    """Audits a single Chat SFT JSON record."""
    issues = []
    stats = {}

    if not isinstance(record, dict) or "messages" not in record:
        return False, ["Missing 'messages' field"], {}

    messages = record["messages"]
    if len(messages) != 3:
        return False, [f"Expected 3 messages, got {len(messages)}"], {}

    sys_msg, user_msg, asst_msg = messages[0], messages[1], messages[2]

    if sys_msg.get("content", "").strip() != REQUIRED_SYSTEM_PROMPT:
        issues.append("System prompt mismatch")

    q_text = user_msg.get("content", "").strip()
    ans_text = asst_msg.get("content", "").strip()

    q_words = len(q_text.split())
    ans_words = len(ans_text.split())

    stats["q_words"] = q_words
    stats["ans_words"] = ans_words

    if q_words < 5:
        issues.append(f"Question too short ({q_words} words)")

    if ans_words < 50:
        issues.append(f"Answer critically short (<50 words: {ans_words})")
    elif ans_words < 80:
        issues.append(f"Answer brief (<80 words: {ans_words})")
    elif ans_words > 450:
        issues.append(f"Answer long (>450 words: {ans_words})")

    ans_lower = ans_text.lower()

    # 1. Pāli term check
    pali_found = [p for p in PALI_TERMS if re.search(r"\b" + re.escape(p) + r"\b", ans_lower)]
    has_pali = len(pali_found) > 0
    stats["pali_terms"] = pali_found
    stats["has_pali"] = has_pali

    # Parenthetical or quotes gloss check (e.g., "(suffering)", "— not-self —")
    has_gloss = bool(re.search(r"\(.*?\)|—.*?—|\".*?\"", ans_text))
    stats["has_gloss"] = has_gloss

    # 2. Simile check
    has_simile = any(re.search(pat, ans_lower) for pat in SIMILE_PATTERNS)
    stats["has_simile"] = has_simile

    # 3. Empathy check
    has_empathy = any(re.search(pat, ans_lower) for pat in EMPATHY_PATTERNS)
    stats["has_empathy"] = has_empathy

    # 4. Phenomenological check
    has_phenomenology = any(re.search(pat, ans_lower) for pat in PHENOMENOLOGICAL_PATTERNS)
    stats["has_phenomenology"] = has_phenomenology

    # Score calculation (0 - 100)
    score = 0
    if has_pali: score += 30
    if has_gloss: score += 10
    if has_simile: score += 25
    if has_empathy: score += 15
    if has_phenomenology: score += 20
    if 100 <= ans_words <= 350: score += 10  # Optimal length bonus (max 100 capped)

    stats["score"] = min(100, score)

    return len(issues) == 0, issues, stats


def audit_file(file_path: str, verbose: bool = False) -> Dict[str, Any]:
    """Audits an entire JSONL dataset file."""
    if not os.path.exists(file_path):
        print(f"[Error] File not found: {file_path}")
        return {"valid": False, "error": "File not found"}

    total_records = 0
    issues_list = []
    ans_word_counts = []
    pali_count = 0
    simile_count = 0
    empathy_count = 0
    phenom_count = 0
    scores = []
    seen_questions = set()
    duplicate_questions = []

    with open(file_path, "r", encoding="utf-8-sig") as f:
        for line_num, line in enumerate(f, start=1):
            line_str = line.strip()
            if not line_str:
                continue
            total_records += 1
            try:
                rec = json.loads(line_str)
            except Exception as e:
                issues_list.append(f"Line {line_num}: JSON decode error: {e}")
                continue

            q = rec.get("messages", [{}, {}])[1].get("content", "").strip().lower()
            if q in seen_questions:
                duplicate_questions.append((line_num, q[:60]))
            seen_questions.add(q)

            is_valid, rec_issues, stats = audit_record(rec, line_num)
            if rec_issues:
                issues_list.extend([f"Line {line_num}: {iss}" for iss in rec_issues])

            ans_word_counts.append(stats.get("ans_words", 0))
            if stats.get("has_pali"): pali_count += 1
            if stats.get("has_simile"): simile_count += 1
            if stats.get("has_empathy"): empathy_count += 1
            if stats.get("has_phenomenology"): phenom_count += 1
            scores.append(stats.get("score", 0))

    if total_records == 0:
        return {"valid": False, "error": "Empty file", "file": file_path}

    avg_words = sum(ans_word_counts) / len(ans_word_counts) if ans_word_counts else 0
    min_words = min(ans_word_counts) if ans_word_counts else 0
    max_words = max(ans_word_counts) if ans_word_counts else 0
    avg_score = sum(scores) / len(scores) if scores else 0

    pali_pct = (pali_count / total_records) * 100
    simile_pct = (simile_count / total_records) * 100
    empathy_pct = (empathy_count / total_records) * 100
    phenom_pct = (phenom_count / total_records) * 100

    report = {
        "file": file_path,
        "filename": os.path.basename(file_path),
        "total_records": total_records,
        "unique_questions": len(seen_questions),
        "duplicate_questions": len(duplicate_questions),
        "avg_words": avg_words,
        "min_words": min_words,
        "max_words": max_words,
        "avg_score": avg_score,
        "pali_pct": pali_pct,
        "simile_pct": simile_pct,
        "empathy_pct": empathy_pct,
        "phenom_pct": phenom_pct,
        "issues": issues_list,
        "duplicate_details": duplicate_questions
    }

    return report


def main():
    parser = argparse.ArgumentParser(description="Audit structural and pedagogical quality of Dhamma datasets.")
    parser.add_argument("file_path", nargs="?", default=None, help="Path to specific .jsonl dataset file")
    parser.add_argument("--all-datasets", action="store_true", help="Audit all datasets in datasets/*.jsonl")
    parser.add_argument("--verbose", action="store_true", help="Print detailed per-record warnings")
    args = parser.parse_args()

    files = []
    if args.all_datasets or (args.file_path is None and not sys.stdin.isatty()):
        files = sorted(glob.glob("datasets/*.jsonl"))
    elif args.file_path:
        files = [args.file_path]
    else:
        files = sorted(glob.glob("datasets/*.jsonl"))

    if not files:
        print("No .jsonl dataset files found to audit.")
        sys.exit(1)

    print(f"\n{'='*95}")
    print(f"{'DHAMMA DATASET STRUCTURAL & PEDAGOGICAL QUALITY AUDIT':^95}")
    print(f"{'='*95}")
    print(f"{'Dataset Name':<42} | {'Pairs':>5} | {'Avg W':>5} | {'Pali %':>6} | {'Simile %':>8} | {'Score':>5} | {'Dupes':>5}")
    print(f"{'-'*95}")

    total_records = 0
    total_dupes = 0
    total_scores = []
    all_reports = []

    for fpath in files:
        report = audit_file(fpath, verbose=args.verbose)
        if "error" in report:
            print(f"{os.path.basename(fpath):<42} | ERROR: {report['error']}")
            continue

        all_reports.append(report)
        total_records += report["total_records"]
        total_dupes += report["duplicate_questions"]
        total_scores.append(report["avg_score"])

        dupe_str = f"{report['duplicate_questions']}" if report['duplicate_questions'] > 0 else "-"
        status_flag = " (!)" if report['duplicate_questions'] > 0 or report['avg_words'] < 90 else ""

        print(
            f"{report['filename'][:42]:<42} | "
            f"{report['total_records']:>5} | "
            f"{report['avg_words']:>5.0f} | "
            f"{report['pali_pct']:>5.1f}% | "
            f"{report['simile_pct']:>7.1f}% | "
            f"{report['avg_score']:>5.1f} | "
            f"{dupe_str:>5}{status_flag}"
        )

    print(f"{'='*95}")
    overall_avg_score = sum(total_scores) / len(total_scores) if total_scores else 0
    print(f"Total Records Audited: {total_records} across {len(all_reports)} datasets")
    print(f"Total Exact Duplicate Questions Found: {total_dupes}")
    print(f"Corpus-wide Average Pedagogical Score: {overall_avg_score:.1f} / 100")
    print(f"{'='*95}\n")

    if args.verbose or total_dupes > 0:
        dupe_files = [r for r in all_reports if r["duplicate_questions"] > 0]
        if dupe_files:
            print(f"[!] Flagged Files with Intra-dataset Duplicates ({len(dupe_files)} files):")
            for r in dupe_files:
                print(f"\n  • {r['filename']} ({r['duplicate_questions']} duplicate questions):")
                for line_num, q_snip in r["duplicate_details"][:5]:
                    print(f"     Line {line_num}: '{q_snip}...'")
                if len(r["duplicate_details"]) > 5:
                    print(f"     ... and {len(r['duplicate_details']) - 5} more duplicates")

    if len(files) == 1 and args.verbose:
        r = all_reports[0]
        if r["issues"]:
            print(f"\n[!] Issues & Quality Notices ({len(r['issues'])}):")
            for iss in r["issues"][:25]:
                print(f"  - {iss}")


if __name__ == "__main__":
    main()
