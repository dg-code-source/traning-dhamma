import argparse
import json
import os
import sys
from typing import Dict, List


def load_chat_sft(file_path: str) -> List[Dict]:
    """Load records from a standard Chat SFT JSONL file."""
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


def to_sharegpt(record: Dict) -> Dict:
    """Convert Chat SFT record to ShareGPT format."""
    messages = record.get("messages", [])
    conversations = []
    for m in messages:
        role = m.get("role")
        content = m.get("content", "")
        if role == "system":
            from_role = "system"
        elif role == "user":
            from_role = "human"
        elif role == "assistant":
            from_role = "gpt"
        else:
            from_role = role
        conversations.append({"from": from_role, "value": content})
    return {"conversations": conversations}


def to_alpaca(record: Dict) -> Dict:
    """Convert Chat SFT record to Alpaca format."""
    messages = record.get("messages", [])
    system_prompt = ""
    instruction = ""
    output = ""

    for m in messages:
        role = m.get("role")
        content = m.get("content", "")
        if role == "system":
            system_prompt = content
        elif role == "user":
            instruction = content
        elif role == "assistant":
            output = content

    return {
        "instruction": instruction,
        "input": "",
        "output": output,
        "system": system_prompt,
    }


def export_dataset(input_file: str, output_file: str, target_format: str) -> int:
    """Export a Chat SFT dataset to ShareGPT or Alpaca format."""
    records = load_chat_sft(input_file)
    if not records:
        print(f"[Error] No records loaded from {input_file}")
        return 0

    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)

    if target_format == "sharegpt":
        converted = [to_sharegpt(r) for r in records]
    elif target_format == "alpaca":
        converted = [to_alpaca(r) for r in records]
    else:
        raise ValueError(f"Unsupported format: {target_format}")

    # Write as JSON array (standard for Alpaca / ShareGPT) or JSONL
    if output_file.endswith(".json"):
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(converted, f, ensure_ascii=False, indent=2)
    else:
        with open(output_file, "w", encoding="utf-8") as f:
            for item in converted:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"[Success] Exported {len(converted)} records to {output_file} (Format: {target_format})")
    return len(converted)


def main():
    parser = argparse.ArgumentParser(
        description="Convert Dhamma Chat SFT datasets into ShareGPT or Alpaca fine-tuning formats."
    )
    parser.add_argument(
        "--input",
        "-i",
        default=None,
        help="Path to input Chat SFT .jsonl file (defaults to datasets/splits/master_dhamma_qa.jsonl).",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Path to output file (.json or .jsonl). If omitted, saves beside input file.",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["sharegpt", "alpaca"],
        default="sharegpt",
        help="Target export format (default: 'sharegpt').",
    )
    parser.add_argument(
        "--all-splits",
        action="store_true",
        help="Export all train, val, and master splits into exports/ folder.",
    )

    args = parser.parse_args()
    root_dir = os.path.abspath(os.path.dirname(__file__))

    if args.all_splits:
        splits = ["master_dhamma_qa", "train", "val"]
        splits_dir = os.path.join(root_dir, "datasets", "splits")
        exports_dir = os.path.join(root_dir, "datasets", "exports")
        os.makedirs(exports_dir, exist_ok=True)
        for s in splits:
            in_file = os.path.join(splits_dir, f"{s}.jsonl")
            if os.path.exists(in_file):
                out_file = os.path.join(exports_dir, f"{s}_{args.format}.json")
                export_dataset(in_file, out_file, args.format)
        return

    input_file = args.input or os.path.join(root_dir, "datasets", "splits", "master_dhamma_qa.jsonl")
    if not os.path.exists(input_file):
        print(f"[Error] Input file not found: {input_file}")
        sys.exit(1)

    if args.output:
        output_file = args.output
    else:
        base, _ = os.path.splitext(input_file)
        output_file = f"{base}_{args.format}.json"

    export_dataset(input_file, output_file, args.format)


if __name__ == "__main__":
    main()
