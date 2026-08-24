#!/usr/bin/env python3
"""
datasets_v2/load_splits.py — Simple, fast loader for V2 Dhamma datasets.
Automatically reads compressed (.jsonl.gz / .json.gz) or uncompressed files.
"""

import gzip
import json
import os
from typing import List, Dict, Generator

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def stream_records(split: str = "train") -> Generator[Dict, None, None]:
    """Stream records one-by-one to save memory."""
    splits_dir = os.path.join(BASE_DIR, "splits")
    if split in ("train", "train_25k"):
        fname = "train_25k.jsonl"
    elif split in ("val", "val_25k", "test"):
        fname = "val_25k.jsonl"
    else:
        fname = "master_25k_dhamma_qa.jsonl"

    raw_path = os.path.join(splits_dir, fname)
    gz_path = raw_path + ".gz"

    if os.path.exists(raw_path):
        with open(raw_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    yield json.loads(line)
    elif os.path.exists(gz_path):
        with gzip.open(gz_path, "rt", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    yield json.loads(line)
    else:
        raise FileNotFoundError(f"Neither {raw_path} nor {gz_path} found.")

def load_records(split: str = "train") -> List[Dict]:
    """Load all records of a split into a Python list."""
    return list(stream_records(split))

if __name__ == "__main__":
    print("Testing datasets_v2 loader:")
    val_data = load_records("val")
    print(f"Successfully loaded {len(val_data):,} validation records!")
    print(f"Sample Question: {val_data[0]['messages'][1]['content'][:120]}...")
    print(f"Sample Answer length: {len(val_data[0]['messages'][2]['content'].split())} words")
