import sys
import json
import os
import argparse

# The canonical system prompt defined in RULES.md (Section 1).
# Every entry in every dataset must use this exact text.
REQUIRED_SYSTEM_PROMPT = (
    "You are a wise and compassionate Dhamma teacher grounded in the Thai Forest "
    "Tradition (in the lineage of Luang Por Chah). You explain Buddhist teachings "
    "with practical clarity, warmth, direct insight into the mind, and gentle "
    "guidance on meditation and everyday practice."
)

# Minimum content thresholds (word counts)
MIN_USER_WORDS = 5
MIN_ASSISTANT_WORDS = 20


def verify_jsonl_dataset(file_path: str) -> bool:
    """Validate that a JSONL file strictly matches the Chat SFT schema from RULES.md."""
    if not os.path.exists(file_path):
        print(f"[Error] File not found: {file_path}")
        return False

    print(f"Checking dataset: {file_path}")
    total_records = 0
    valid_records = 0
    errors = []
    assistant_word_counts = []

    with open(file_path, "r", encoding="utf-8-sig") as f:
        for idx, line in enumerate(f, start=1):
            line_str = line.strip()
            if not line_str:
                errors.append(f"Line {idx}: Empty line detected.")
                continue

            total_records += 1
            record_errors = []

            try:
                record = json.loads(line_str)
            except json.JSONDecodeError as e:
                errors.append(f"Line {idx}: Invalid JSON syntax - {e}")
                continue

            # Schema checks
            if not isinstance(record, dict) or "messages" not in record:
                errors.append(f"Line {idx}: Missing top-level 'messages' key.")
                continue

            messages = record["messages"]
            if not isinstance(messages, list) or len(messages) < 3:
                errors.append(
                    f"Line {idx}: 'messages' must be a list with exactly 3 entries "
                    f"(system, user, assistant). Found {len(messages) if isinstance(messages, list) else 'non-list'}."
                )
                continue

            # Validate role sequence: must be exactly ["system", "user", "assistant"]
            roles = [m.get("role") for m in messages if isinstance(m, dict)]
            if roles != ["system", "user", "assistant"]:
                errors.append(
                    f"Line {idx}: Unexpected role sequence: {roles}. "
                    f"Expected ['system', 'user', 'assistant']."
                )
                continue

            # Validate each message entry
            for m_idx, m in enumerate(messages):
                if not isinstance(m, dict):
                    record_errors.append(f"Line {idx}, message {m_idx}: Message entry is not a dictionary.")
                elif not m.get("content") or not str(m.get("content")).strip():
                    record_errors.append(f"Line {idx}, role '{m.get('role')}': Content is empty or missing.")

            # Validate system prompt matches RULES.md
            system_content = messages[0].get("content", "").strip()
            if system_content != REQUIRED_SYSTEM_PROMPT:
                record_errors.append(
                    f"Line {idx}: System prompt does not match RULES.md. "
                    f"Got: '{system_content[:80]}...'"
                )

            # Validate minimum content lengths
            user_content = messages[1].get("content", "").strip()
            user_words = len(user_content.split())
            if user_words < MIN_USER_WORDS:
                record_errors.append(
                    f"Line {idx}: User question too short ({user_words} words, minimum {MIN_USER_WORDS})."
                )

            assistant_content = messages[2].get("content", "").strip()
            assistant_words = len(assistant_content.split())
            if assistant_words < MIN_ASSISTANT_WORDS:
                record_errors.append(
                    f"Line {idx}: Assistant answer too short ({assistant_words} words, minimum {MIN_ASSISTANT_WORDS})."
                )

            if record_errors:
                errors.extend(record_errors)
            else:
                valid_records += 1
                assistant_word_counts.append(assistant_words)

    if errors:
        print(f"\n[FAILED] Found {len(errors)} error(s) across {total_records} records:")
        for err in errors[:20]:
            print(f"  - {err}")
        if len(errors) > 20:
            print(f"  ... and {len(errors) - 20} more errors.")
        if valid_records > 0:
            print(f"\n  {valid_records}/{total_records} records passed validation.")
        return False

    if total_records == 0:
        print("[FAILED] File is empty — no records found.")
        return False

    avg_words = sum(assistant_word_counts) / len(assistant_word_counts) if assistant_word_counts else 0
    min_words = min(assistant_word_counts) if assistant_word_counts else 0
    max_words = max(assistant_word_counts) if assistant_word_counts else 0

    print(f"[PASSED] Verified {valid_records} records successfully!")
    print(f"         All records strictly adhere to the Chat SFT specification.")
    print(f"         Assistant answer stats: avg={avg_words:.0f}, min={min_words}, max={max_words} words")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify Dhamma JSONL dataset format.")
    parser.add_argument("file_path", help="Path to the .jsonl dataset file")
    args = parser.parse_args()

    success = verify_jsonl_dataset(args.file_path)
    sys.exit(0 if success else 1)
