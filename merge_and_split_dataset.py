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
        nargs="+",
        default=["datasets"],
        help="Directory or directories containing source .jsonl datasets (default: ['datasets']).",
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
    parser.add_argument(
        "--master-name",
        default="master_dhamma_qa.jsonl",
        help="Name for master merged dataset (default: 'master_dhamma_qa.jsonl').",
    )

    args = parser.parse_args()

    # Find all .jsonl files in all specified datasets_dir
    files = []
    for d in args.datasets_dir:
        if os.path.exists(d):
            for root, _, fnames in os.walk(d):
                for f in sorted(fnames):
                    if f.endswith(".jsonl") and not f.startswith("master_") and f not in ("train.jsonl", "val.jsonl", "train_25k.jsonl", "val_25k.jsonl"):
                        files.append(os.path.join(root, f))

    if not files:
        print(f"[Error] No .jsonl dataset files found in {args.datasets_dir}.")
        sys.exit(1)

    print(f"Found {len(files)} dataset files to merge:")
    for f in files[:10]:
        print(f" - {f}")
    if len(files) > 10:
        print(f" ... and {len(files)-10} more files")

    # Custom master path override
    os.makedirs(args.output_dir, exist_ok=True)
    all_records: List[Dict] = []
    seen_keys: Set[str] = set()
    duplicate_count = 0

    for path in files:
        records = load_jsonl_records(path)
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
        sys.exit(1)

    random.seed(args.seed)
    random.shuffle(all_records)

    master_path = os.path.join(args.output_dir, args.master_name)
    with open(master_path, "w", encoding="utf-8") as f:
        for rec in all_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"[Created] Master dataset: {master_path} ({total} records)")

    if not args.master_only and args.val_ratio > 0.0:
        val_count = max(1, int(total * args.val_ratio))
        train_count = total - val_count
        val_records = all_records[:val_count]
        train_records = all_records[val_count:]

        train_filename = "train_25k.jsonl" if "25k" in args.master_name else "train.jsonl"
        val_filename = "val_25k.jsonl" if "25k" in args.master_name else "val.jsonl"

        train_path = os.path.join(args.output_dir, train_filename)
        val_path = os.path.join(args.output_dir, val_filename)

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


if __name__ == "__main__":
    main()
