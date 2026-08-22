import json
import os
import sys
from typing import Dict, List


def analyze_jsonl(file_path: str) -> Dict:
    """Extract statistics from a single JSONL file."""
    total_records = 0
    user_words = []
    assistant_words = []

    with open(file_path, "r", encoding="utf-8-sig") as f:
        for line in f:
            line_str = line.strip()
            if not line_str:
                continue
            try:
                rec = json.loads(line_str)
                messages = rec.get("messages", [])
                if len(messages) >= 3:
                    u_text = messages[1].get("content", "")
                    a_text = messages[2].get("content", "")
                    user_words.append(len(u_text.split()))
                    assistant_words.append(len(a_text.split()))
                    total_records += 1
            except json.JSONDecodeError:
                continue

    return {
        "file": os.path.basename(file_path),
        "path": file_path,
        "count": total_records,
        "avg_user_words": sum(user_words) / len(user_words) if user_words else 0,
        "avg_assistant_words": sum(assistant_words) / len(assistant_words) if assistant_words else 0,
        "total_assistant_words": sum(assistant_words),
    }


def main():
    root_dir = os.path.abspath(os.path.dirname(__file__))
    datasets_dir = os.path.join(root_dir, "datasets")
    transcripts_dir = os.path.join(root_dir, "transcripts")
    extracted_dir = os.path.join(root_dir, "documents", "extracted")

    print("\n" + "=" * 80)
    print("                      DHAMMA QA CORPUS INVENTORY & STATUS")
    print("=" * 80)

    # 1. Dataset statistics
    dataset_files = []
    if os.path.exists(datasets_dir):
        for f in sorted(os.listdir(datasets_dir)):
            if f.endswith(".jsonl") and not f.startswith("master_") and f not in ("train.jsonl", "val.jsonl"):
                dataset_files.append(os.path.join(datasets_dir, f))

    stats_list = [analyze_jsonl(fp) for fp in dataset_files]
    total_qa = sum(s["count"] for s in stats_list)
    total_words = sum(s["total_assistant_words"] for s in stats_list)

    print(f"\n[Generated Datasets ({len(stats_list)} files)]")
    print(f"{'Dataset Name':<50} | {'QA Pairs':<8} | {'Avg Words':<10}")
    print("-" * 75)
    for s in stats_list:
        print(f"{s['file'][:48]:<50} | {s['count']:<8} | {s['avg_assistant_words']:<10.0f}")
    print("-" * 75)
    print(f"{'TOTAL CORPUS':<50} | {total_qa:<8} | {total_words / total_qa if total_qa else 0:<10.0f}")
    print(f"Total assistant training words: {total_words:,} words (~{int(total_words * 1.35):,} tokens)")

    # 2. Extracted Books Inventory
    print("\n" + "-" * 80)
    print("[Extracted EPUB Books]")
    if os.path.exists(extracted_dir):
        books = sorted(os.listdir(extracted_dir))
        for b in books:
            b_path = os.path.join(extracted_dir, b)
            if os.path.isdir(b_path):
                meta_file = os.path.join(b_path, "metadata.json")
                if os.path.exists(meta_file):
                    with open(meta_file, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    print(f" • {meta.get('title', b)} ({meta.get('author', 'Unknown')}) - {meta.get('total_words', 0):,} words, {meta.get('total_chapters', 0)} chapters")
                else:
                    print(f" • {b} (Extracted)")
    else:
        print(" (None)")

    # 3. YouTube Transcripts Inventory
    print("\n" + "-" * 80)
    print("[Extracted YouTube Transcripts]")
    if os.path.exists(transcripts_dir):
        transcripts = [f for f in sorted(os.listdir(transcripts_dir)) if f.endswith(".txt")]
        for t in transcripts:
            t_path = os.path.join(transcripts_dir, t)
            with open(t_path, "r", encoding="utf-8", errors="ignore") as f:
                w_count = len(f.read().split())
            print(f" • {t[:-4]} ({w_count:,} words)")
    else:
        print(" (None)")

    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
