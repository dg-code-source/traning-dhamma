import argparse
import glob
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
    parser = argparse.ArgumentParser(description="Export Chat SFT datasets to ShareGPT or Alpaca format.")
    parser.add_argument("--input", "-i", default=None, help="Path to input .jsonl dataset file.")
    parser.add_argument("--output", "-o", default=None, help="Path to output export file.")
    parser.add_argument(
        "--format", "-f", choices=["sharegpt", "alpaca"], default="sharegpt", help="Target export format."
    )
    parser.add_argument(
        "--splits-dir",
        default="datasets/splits",
        help="Directory containing master, train, and val splits (default: 'datasets/splits').",
    )
    parser.add_argument(
        "--output-dir",
        default="datasets/exports",
        help="Directory to save exported files when using --all-splits (default: 'datasets/exports').",
    )
    parser.add_argument(
        "--all-splits",
        action="store_true",
        help="Export all standard splits (master, train, val) automatically.",
    )

    args = parser.parse_args()

    if args.all_splits:
        splits_dir = args.splits_dir
        exports_dir = args.output_dir

        # Identify files in splits_dir
        split_files = glob.glob(os.path.join(splits_dir, "*.jsonl"))
        if not split_files:
            print(f"[Error] No .jsonl files found in {splits_dir}")
            sys.exit(1)

        for in_p in split_files:
            base = os.path.splitext(os.path.basename(in_p))[0]
            ext = ".json"
            out_p = os.path.join(exports_dir, f"{base}_{args.format}{ext}")
            export_dataset(in_p, out_p, args.format)
        return

    if not args.input or not args.output:
        print("[Error] Must specify either --all-splits or both --input and --output.")
        parser.print_help()
        sys.exit(1)

    export_dataset(args.input, args.output, args.format)


if __name__ == "__main__":
    main()
