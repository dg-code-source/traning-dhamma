#!/usr/bin/env python3
"""
datasets_v5/load_splits.py — Fast, transparent loader for Dataset-V5.
Reads compressed (.jsonl.gz) or uncompressed files seamlessly.
"""

import gzip
import json
import os
from typing import List, Dict, Generator

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def stream_records(split: str = "train") -> Generator[Dict, None, None]:
    splits_dir = os.path.join(BASE_DIR, "splits")
    if split in ("train", "train_v5"):
        fname = "train_v5.jsonl"
    elif split in ("val", "val_v5", "test"):
        fname = "val_v5.jsonl"
    else:
        fname = "master_v5_aligned.jsonl"

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
    return list(stream_records(split))

if __name__ == "__main__":
    val_data = load_records("val")
    print(f"Successfully loaded {len(val_data):,} V5 validation records!")
    print(f"Sample Question: {val_data[0]['messages'][1]['content'][:120]}...")
    print(f"Sample Answer word count: {len(val_data[0]['messages'][2]['content'].split())} words")
