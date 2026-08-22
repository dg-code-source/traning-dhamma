import argparse
import json
import os
import re
import sys
from typing import Any, Dict, List, Tuple, Union

# Canonical system prompt defined in RULES.md (Section 1)
REQUIRED_SYSTEM_PROMPT = (
    "You are a wise and compassionate Dhamma teacher grounded in the Thai Forest "
    "Tradition (in the lineage of Luang Por Chah). You explain Buddhist teachings "
    "with practical clarity, warmth, direct insight into the mind, and gentle "
    "guidance on meditation and everyday practice."
)


def naturalize_question(question: str, min_words: int = 5) -> str:
    """
    Sanitize and naturalize a user question to ensure authentic seeker phrasing
    and compliance with minimum length requirements (>= 5 words).
    """
    q = str(question).strip(" #*\t\r\n")
    # Remove chapter numbering suffixes like (12) or [3]
    q = re.sub(r"\s*[\(\[]\d+[\)\]]$", "", q).strip()

    # Pre-mapped standard short question expansions
    common_short_maps = {
        "what is enlightenment": "Ajahn, what is enlightenment and what does it mean to be enlightened?",
        "who was the buddha": "Ajahn, could you explain who the Buddha was historically?",
        "what does “buddha” mean": "Ajahn, what does the title 'Buddha' actually mean?",
        "what does \"buddha\" mean": "Ajahn, what does the title 'Buddha' actually mean?",
        "what does 'buddha' mean": "Ajahn, what does the title 'Buddha' actually mean?",
        "what is merit": "Ajahn, what is the meaning and purpose of merit in Buddhism?",
        "why meditate": "Ajahn, why should we meditate and what are its main benefits?",
        "what is mindfulness": "Ajahn, what is mindfulness and how is it defined in Buddhism?",
        "what are defilements": "Ajahn, what are defilements (kilesa) and how do they affect the mind?",
        "what is the vinaya": "Ajahn, what is the Vinaya and why is it important for monastics?",
        "dāna (giving)": "Ajahn, what is the role and importance of dāna (giving) on the Buddhist path?",
        "sīla (morality)": "Ajahn, what is the significance of sīla (morality) in spiritual practice?",
        "bhāvanā (mental cultivation)": "Ajahn, what does bhāvanā (mental cultivation or meditation) entail?",
    }

    q_normalized = q.lower().rstrip("?. ")
    if q_normalized in common_short_maps:
        return common_short_maps[q_normalized]

    words = q.split()
    if len(words) < min_words:
        # Naturalize generic short questions
        if q_normalized.startswith("what is ") or q_normalized.startswith("what are "):
            q = f"Ajahn, could you explain {q[0].lower() + q[1:].rstrip('?.')} in Buddhist practice?"
        elif q_normalized.startswith("why "):
            q = f"Ajahn, could you explain {q[0].lower() + q[1:].rstrip('?.')} from the perspective of Dhamma?"
        elif q_normalized.startswith("how "):
            q = f"Ajahn, could you explain {q[0].lower() + q[1:].rstrip('?.')} in our daily practice?"
        elif q_normalized.startswith("who was ") or q_normalized.startswith("who is "):
            q = f"Ajahn, could you explain {q[0].lower() + q[1:].rstrip('?.')}?"
        else:
            q = f"Ajahn, could you please explain: {q.rstrip('?.')}?"

    words_after = q.split()
    # Add courteous teacher address if question is short
    if (
        not q.lower().startswith("ajahn")
        and not q.lower().startswith("venerable")
        and not q.lower().startswith("bhante")
        and len(words_after) < 8
    ):
        q = f"Ajahn, {q[0].lower() + q[1:]}"

    if not q.endswith("?") and not q.endswith("."):
        q = q + "?"

    return q


def format_record(
    user_content: str,
    assistant_content: str,
    system_prompt: str = REQUIRED_SYSTEM_PROMPT,
    auto_naturalize: bool = True,
) -> Dict[str, Any]:
    """Create a standardized Chat SFT record dict."""
    user_q = naturalize_question(user_content) if auto_naturalize else str(user_content).strip()
    return {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_q},
            {"role": "assistant", "content": str(assistant_content).strip()},
        ]
    }


def build_dataset(
    qa_pairs: List[Union[Tuple[str, str], List[str], Dict[str, str]]],
    output_path: str,
    system_prompt: str = REQUIRED_SYSTEM_PROMPT,
    auto_verify: bool = True,
    auto_naturalize: bool = True,
) -> bool:
    """
    Compile a list of QA pairs into a valid Chat SFT JSONL dataset.

    Args:
        qa_pairs: List of (question, answer) tuples or dicts with 'user'/'assistant' or 'question'/'answer'.
        output_path: Target path for the .jsonl file.
        system_prompt: System prompt string to use across all entries.
        auto_verify: If True, automatically runs verify_jsonl_dataset after writing.
        auto_naturalize: If True, automatically sanitizes and ensures user questions meet length & persona standards.

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

        records.append(
            format_record(
                q,
                a,
                system_prompt=system_prompt,
                auto_naturalize=auto_naturalize,
            )
        )

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
    auto_naturalize: bool = True,
) -> bool:
    """Append a single QA pair to an existing or new JSONL dataset."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    rec = format_record(
        user_content,
        assistant_content,
        system_prompt=system_prompt,
        auto_naturalize=auto_naturalize,
    )

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
    parser.add_argument(
        "--no-naturalize",
        action="store_true",
        help="Do not auto-naturalize short questions.",
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
        auto_naturalize=not args.no_naturalize,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
