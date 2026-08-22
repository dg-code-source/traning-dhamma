import argparse
import json
import os
import random
import sys
from typing import Dict, List, Set, Tuple

try:
    from verify_dataset import verify_jsonl_dataset
except ImportError:
    verify_jsonl_dataset = None


def load_jsonl_records(file_path: str) -> List[Dict]:
    """Load all records from a JSONL file."""
    records = []
    with open(file_path, "r", encoding="utf-8-sig") as f:
        for line in f:
            line_str = line.strip()
            if line_str:
                try:
                    records.append(json.loads(line_str))
                except json.JSONDecodeError:
                    continue
    return records


def get_record_key(record: Dict) -> str:
    """Extract question text as a deduplication key."""
    messages = record.get("messages", [])
    if len(messages) >= 2:
        return messages[1].get("content", "").strip().lower()
    return ""


def merge_and_split(
    input_paths: List[str],
    output_dir: str,
    val_ratio: float = 0.1,
    seed: int = 42,
    master_only: bool = False,
) -> Tuple[int, int, int]:
    """
    Merge multiple dataset files, deduplicate, and optionally split into train/val.
    """
    os.makedirs(output_dir, exist_ok=True)
    all_records: List[Dict] = []
    seen_keys: Set[str] = set()
    duplicate_count = 0

    for path in input_paths:
        if not os.path.exists(path):
            print(f"[Warning] File not found, skipping: {path}")
            continue

        records = load_jsonl_records(path)
        print(f"Loaded {len(records)} records from {os.path.basename(path)}")

        for rec in records:
            key = get_record_key(rec)
            if key in seen_keys and key != "":
                duplicate_count += 1
                continue
            seen_keys.add(key)
            all_records.append(rec)

    total = len(all_records)
    print(f"\nTotal unique records: {total} (removed {duplicate_count} duplicates)")

    if total == 0:
        print("[Error] No records to write.")
        return 0, 0, 0

    random.seed(seed)
    random.shuffle(all_records)

    # Master full dataset
    master_path = os.path.join(output_dir, "master_dhamma_qa.jsonl")
    with open(master_path, "w", encoding="utf-8") as f:
        for rec in all_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"[Created] Master dataset: {master_path} ({total} records)")

    if master_only or val_ratio <= 0.0:
        if verify_jsonl_dataset:
            verify_jsonl_dataset(master_path)
        return total, total, 0

    val_count = max(1, int(total * val_ratio))
    train_count = total - val_count

    val_records = all_records[:val_count]
    train_records = all_records[val_count:]

    train_path = os.path.join(output_dir, "train.jsonl")
    val_path = os.path.join(output_dir, "val.jsonl")

    with open(train_path, "w", encoding="utf-8") as f:
        for rec in train_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    with open(val_path, "w", encoding="utf-8") as f:
        for rec in val_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"[Created] Train split: {train_path} ({train_count} records)")
    print(f"[Created] Val split:   {val_path} ({val_count} records)")

    if verify_jsonl_dataset:
        print("\n--- Verifying Splits ---")
        verify_jsonl_dataset(train_path)
        verify_jsonl_dataset(val_path)

    return total, train_count, val_count


def main():
    parser = argparse.ArgumentParser(
        description="Merge multiple Dhamma Chat SFT datasets, deduplicate, and split into train/val sets."
    )
    parser.add_argument(
        "--datasets-dir",
        "-d",
        default="datasets",
        help="Directory containing source .jsonl datasets (default: 'datasets').",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        default="datasets/splits",
        help="Output directory for merged and split datasets (default: 'datasets/splits').",
    )
    parser.add_argument(
        "--val-ratio",
        "-v",
        type=float,
        default=0.1,
        help="Validation split ratio between 0.0 and 0.5 (default: 0.1).",
    )
    parser.add_argument(
        "--seed",
        "-s",
        type=int,
        default=42,
        help="Random seed for shuffling (default: 42).",
    )
    parser.add_argument(
        "--master-only",
        action="store_true",
        help="Create only the merged master dataset without train/val splits.",
    )

    args = parser.parse_args()

    # Find all .jsonl files in datasets_dir, excluding master/splits themselves
    files = []
    for f in sorted(os.listdir(args.datasets_dir)):
        if f.endswith(".jsonl") and not f.startswith("master_") and f not in ("train.jsonl", "val.jsonl"):
            files.append(os.path.join(args.datasets_dir, f))

    if not files:
        print(f"[Error] No .jsonl dataset files found in '{args.datasets_dir}'.")
        sys.exit(1)

    print(f"Found {len(files)} dataset files to merge:")
    for f in files:
        print(f" - {f}")

    merge_and_split(
        input_paths=files,
        output_dir=args.output_dir,
        val_ratio=args.val_ratio,
        seed=args.seed,
        master_only=args.master_only,
    )


if __name__ == "__main__":
    main()
