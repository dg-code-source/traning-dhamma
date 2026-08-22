import argparse
import json
import os
import sys
from typing import Any, Dict, List, Tuple, Union

# Canonical system prompt defined in RULES.md (Section 1)
REQUIRED_SYSTEM_PROMPT = (
    "You are a wise and compassionate Dhamma teacher grounded in the Thai Forest "
    "Tradition (in the lineage of Luang Por Chah). You explain Buddhist teachings "
    "with practical clarity, warmth, direct insight into the mind, and gentle "
    "guidance on meditation and everyday practice."
)


def format_record(
    user_content: str,
    assistant_content: str,
    system_prompt: str = REQUIRED_SYSTEM_PROMPT,
) -> Dict[str, Any]:
    """Create a standardized Chat SFT record dict."""
    return {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": str(user_content).strip()},
            {"role": "assistant", "content": str(assistant_content).strip()},
        ]
    }


def build_dataset(
    qa_pairs: List[Union[Tuple[str, str], List[str], Dict[str, str]]],
    output_path: str,
    system_prompt: str = REQUIRED_SYSTEM_PROMPT,
    auto_verify: bool = True,
) -> bool:
    """
    Compile a list of QA pairs into a valid Chat SFT JSONL dataset.

    Args:
        qa_pairs: List of (question, answer) tuples or dicts with 'user'/'assistant' or 'question'/'answer'.
        output_path: Target path for the .jsonl file.
        system_prompt: System prompt string to use across all entries.
        auto_verify: If True, automatically runs verify_jsonl_dataset after writing.

    Returns:
        bool: True if writing (and optional verification) succeeded.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    records = []
    for idx, item in enumerate(qa_pairs, start=1):
        if isinstance(item, (tuple, list)) and len(item) >= 2:
            q, a = item[0], item[1]
        elif isinstance(item, dict):
            q = item.get("user") or item.get("question") or item.get("q")
            a = item.get("assistant") or item.get("answer") or item.get("a")
            if not q or not a:
                print(f"[Error] Item {idx} missing question or answer: {item}")
                return False
        else:
            print(f"[Error] Item {idx} is invalid format: {type(item)}")
            return False

        records.append(format_record(q, a, system_prompt=system_prompt))

    with open(output_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"[Success] Wrote {len(records)} records to {output_path}")

    if auto_verify:
        try:
            from verify_dataset import verify_jsonl_dataset

            return verify_jsonl_dataset(output_path)
        except ImportError:
            print("[Warning] verify_dataset.py not found in path, skipping automatic verification.")

    return True


def append_to_dataset(
    output_path: str,
    user_content: str,
    assistant_content: str,
    system_prompt: str = REQUIRED_SYSTEM_PROMPT,
    auto_verify: bool = False,
) -> bool:
    """Append a single QA pair to an existing or new JSONL dataset."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    rec = format_record(user_content, assistant_content, system_prompt=system_prompt)

    with open(output_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    if auto_verify:
        try:
            from verify_dataset import verify_jsonl_dataset

            return verify_jsonl_dataset(output_path)
        except ImportError:
            pass

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Build a standardized Chat SFT JSONL dataset from raw QA inputs."
    )
    parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Path to input JSON file containing array of QA pairs (list of [q, a] or [{'user': ..., 'assistant': ...}]).",
    )
    parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="Path to output .jsonl dataset file.",
    )
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip automatic verification after generation.",
    )

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"[Error] Input file not found: {args.input}")
        sys.exit(1)

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        print(f"[Error] Input JSON must be a list of QA pairs. Found: {type(data)}")
        sys.exit(1)

    success = build_dataset(
        data,
        args.output,
        auto_verify=not args.no_verify,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
