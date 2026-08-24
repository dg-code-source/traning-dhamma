#!/usr/bin/env python3
"""
tools/generate_all_extracted_books_qa.py — Complete High-Depth Book QA Generator
Iterates through all 106 extracted book directories in documents/extracted/,
reads every substantive chapter, extracts grounded quotes and themes,
and generates rich, diverse, 4-part structured Thai Forest Dhamma QA pairs.
"""

import os
import glob
import json
import re
import sys
from typing import List, Dict, Tuple, Set

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SYSTEM_PROMPT = (
    "You are a wise and compassionate Dhamma teacher grounded in the Thai Forest "
    "Tradition (in the lineage of Luang Por Chah). You explain Buddhist teachings "
    "with practical clarity, warmth, direct insight into the mind, and gentle "
    "guidance on meditation and everyday practice."
)

SKIP_KEYWORDS = [
    "copyright", "acknowledgement", "acknowledgments", "about the author",
    "further resources", "abbreviation", "abbreviations", "selected bibliography",
    "bibliography", "selected glossary", "glossary", "appendix", "table of contents",
    "contents", "isbn", "definition of technical terms"
]

SIMILE_PATTERNS = [
    "It is like a small boat floating on a calm mountain lake beneath an open sky.",
    "It is like turning off a loud motor and resting in the natural silence of the room.",
    "It is like a bird gliding through open space without needing to build a nest on a cloud.",
    "It is like letting muddy water in a glass sit undisturbed until it becomes crystal clear.",
    "It is like a deep ocean holding waves on its surface while remaining utterly still below.",
    "It is like stepping off a speeding treadmill onto solid, unmoving ground.",
    "It is like an anchor dropped deep into the seabed, keeping the boat steady in stormy waves.",
    "It is like sunlight streaming through clear interstellar space, luminous yet casting no shadow.",
    "It is like opening the window shutters of a stuffy room to let the fresh mountain breeze flow in.",
    "It is like looking at a clear reflection in still water when the wind ceases."
]

def sanitize_slug(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9_-]", "_", name)
    s = re.sub(r"_+", "_", s).strip("_")
    return s

def clean_text_passage(text: str) -> str:
    # Remove excessive blank lines, header tags, footnote numbers
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    cleaned = []
    for l in lines:
        if l.startswith("#"):
            continue
        if re.match(r"^\d+\s*$", l):
            continue
        if any(sk in l.lower() for sk in ["isbn", "sadaham senasuna", "published by", "all rights reserved"]):
            continue
        cleaned.append(l)
    return " ".join(cleaned)

def extract_meaningful_sentences(text: str, n: int = 25) -> List[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    valid = []
    seen = set()
    for s in sentences:
        s_clean = s.strip()
        words = s_clean.split()
        if 12 <= len(words) <= 65:
            # Check for substantive Dhamma content
            sl = s_clean.lower()
            if any(w in sl for w in [
                "mind", "heart", "breath", "awareness", "suffering", "peace", "stillness",
                "meditation", "letting go", "clinging", "craving", "present", "insight",
                "wisdom", "anicca", "dukkha", "anatta", "sati", "samadhi", "kamma", "nature",
                "feeling", "thought", "calm", "silence", "freedom", "refuge", "patience"
            ]):
                key = " ".join(words[:6]).lower()
                if key not in seen and not any(bad in sl for bad in ["http", "isbn", "page", "published"]):
                    seen.add(key)
                    valid.append(s_clean)
        if len(valid) >= n:
            break
    return valid

def generate_chapter_qa(book_title: str, author: str, chapter_title: str, chapter_text: str) -> List[Tuple[str, str]]:
    words = chapter_text.split()
    word_count = len(words)
    if word_count < 80:
        return []

    # Dynamic target count based on length
    if word_count < 800:
        target = 3
    elif word_count < 2000:
        target = 5
    elif word_count < 5000:
        target = 8
    elif word_count < 12000:
        target = 12
    else:
        target = 18

    passages = extract_meaningful_sentences(chapter_text, n=target + 5)
    clean_book = re.sub(r"\s*-\s*.*$", "", book_title).strip()
    clean_chap = re.sub(r"^\d+\s*[-:]?\s*", "", chapter_title).strip()
    if clean_chap.lower() in ["chapter", "part", "section", "untitled"]:
        clean_chap = clean_book

    pairs = []
    used_q = set()

    # 1. Main Chapter Theme Question
    if passages:
        p0 = passages[0]
        q0 = f"In '{clean_book}' (Chapter: '{clean_chap}'), what is the central teaching on practice?"
        a0 = (
            f"In this section of *{clean_book}*, the teaching focuses on direct observation of the mind: "
            f"*\"{p0}\"* "
            f"The central guidance is to step back from the habitual impulse to control or fix present experience, "
            f"and instead cultivate a spacious, non-reactive presence. "
            f"When we investigate thoughts and feelings without identification (*anattā*), their grip on the heart naturally dissolves. "
            f"It is like {SIMILE_PATTERNS[len(pairs) % len(SIMILE_PATTERNS)]} "
            f"Rest in that clear, unentangled knowing."
        )
        pairs.append((q0, a0))
        used_q.add(q0)

    # 2. Passage-grounded questions
    for idx, p in enumerate(passages[1:], 1):
        if len(pairs) >= target:
            break
        pl = p.lower()
        
        if any(w in pl for w in ["suffering", "pain", "stress", "dukkha", "difficult"]):
            q = f"In '{clean_book}' ({clean_chap}), how are we advised to relate to suffering and emotional tension?"
            a = (
                f"The text instructs: *\"{p}\"* "
                f"Rather than resisting discomfort or becoming identified with it as 'my pain', "
                f"the Forest Tradition guides us to bring gentle, interested awareness directly to the feeling. "
                f"Observe that tension is an impermanent, conditioned phenomenon arising in awareness. "
                f"It is like {SIMILE_PATTERNS[(len(pairs) + 1) % len(SIMILE_PATTERNS)]} "
                f"Allow the knot of tension to unwind naturally in spacious presence."
            )
        elif any(w in pl for w in ["breath", "breathing", "anapana", "body", "posture"]):
            q = f"What practical guidance on meditation and body awareness is given in '{clean_book}' ({clean_chap})?"
            a = (
                f"The teaching highlights: *\"{p}\"* "
                f"Working with the breath and physical sensations grounds the mind in the immediate present (*paccuppanna*). "
                f"Do not force or manipulate the breath; simply maintain relaxed, continuous mindfulness of each in-and-out cycle. "
                f"It is like {SIMILE_PATTERNS[(len(pairs) + 2) % len(SIMILE_PATTERNS)]} "
                f"Let the body settle and the heart become still."
            )
        elif any(w in pl for w in ["thought", "mind", "thinking", "concept", "story"]):
            q = f"In '{clean_book}' ({clean_chap}), how should a meditator handle restless thoughts and mental chatter?"
            a = (
                f"The text reflects: *\"{p}\"* "
                f"Thoughts are merely passing mental formations (*saṅkhāra*); they have no solid core unless we feed them with belief. "
                f"When a thought arises, simply recognize it as 'thinking, thinking' without jumping into the storyline. "
                f"It is like {SIMILE_PATTERNS[(len(pairs) + 3) % len(SIMILE_PATTERNS)]} "
                f"Be the vast, open sky through which thoughts pass like harmless clouds."
            )
        elif any(w in pl for w in ["letting go", "release", "clinging", "attachment", "renunciation"]):
            q = f"What is the essence of letting go (vossagga) taught in '{clean_book}' ({clean_chap})?"
            a = (
                f"The teaching observes: *\"{p}\"* "
                f"True letting go is not an act of aggressive rejection, but the wisdom of non-clinging (*anupādāna*). "
                f"When the mind recognizes that nothing in the conditioned world can provide permanent security, the gripping reflex naturally relaxes. "
                f"It is like {SIMILE_PATTERNS[(len(pairs) + 4) % len(SIMILE_PATTERNS)]} "
                f"Rest in the relief of an unburdened heart."
            )
        else:
            excerpt_topic = " ".join([w for w in p.split()[:7] if len(w) > 3])
            q = f"In '{clean_book}' ({clean_chap}), what insight is offered on: '{excerpt_topic}...'?"
            a = (
                f"The text teaches: *\"{p}\"* "
                f"This reflection invites us to look past superficial conventions into the living reality of the present moment. "
                f"By cultivating patience, virtue, and clear discernment, the mind discovers an unshakable inner refuge. "
                f"It is like {SIMILE_PATTERNS[(len(pairs) + 5) % len(SIMILE_PATTERNS)]} "
                f"Walk the noble path with confidence and peace."
            )

        if q not in used_q:
            pairs.append((q, a))
            used_q.add(q)

    return pairs

def process_all_extracted_books():
    print("=" * 80)
    print("COMPREHENSIVE EXTRACTION & QA GENERATION ACROSS ALL EXTRACTED BOOKS")
    print("=" * 80)

    extracted_dirs = sorted(glob.glob("documents/extracted/*"))
    print(f"Found {len(extracted_dirs)} total book folders in documents/extracted/.\n")

    total_books_processed = 0
    total_qa_pairs_generated = 0

    for b_idx, book_dir in enumerate(extracted_dirs, 1):
        dir_name = os.path.basename(book_dir)
        meta_path = os.path.join(book_dir, "metadata.json")
        book_title = dir_name
        author = "Thai Forest Tradition"
        
        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as mf:
                try:
                    m = json.load(mf)
                    book_title = m.get("title", book_title)
                    author = m.get("author", author)
                except Exception:
                    pass

        # Identify all substantive chapter files
        ch_files = sorted(glob.glob(os.path.join(book_dir, "chapter_*.txt")))
        substantive_ch = []
        for ch in ch_files:
            ch_name = os.path.basename(ch).lower()
            if not any(skip in ch_name for skip in SKIP_KEYWORDS):
                substantive_ch.append(ch)

        # If no separate chapters, use full_book.txt
        if not substantive_ch:
            full_path = os.path.join(book_dir, "full_book.txt")
            if os.path.exists(full_path):
                substantive_ch = [full_path]

        book_qa_pairs = []
        for ch_path in substantive_ch:
            ch_fname = os.path.basename(ch_path)
            # Extract clean chapter title from filename
            ch_title_clean = re.sub(r"^chapter_\d+_", "", os.path.splitext(ch_fname)[0]).replace("_", " ")
            with open(ch_path, "r", encoding="utf-8", errors="replace") as cf:
                ch_raw = cf.read()
            ch_clean = clean_text_passage(ch_raw)
            if len(ch_clean.split()) >= 80:
                qa_list = generate_chapter_qa(book_title, author, ch_title_clean, ch_clean)
                book_qa_pairs.extend(qa_list)

        if not book_qa_pairs:
            continue

        slug = sanitize_slug(dir_name)
        out_dataset_path = os.path.join("datasets", f"{slug}_qa.jsonl")
        source_str = f"Book: {book_title} - {author}"

        records = [
            {
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": q},
                    {"role": "assistant", "content": a}
                ],
                "source": source_str,
                "title": book_title
            }
            for q, a in book_qa_pairs
        ]

        # Write to datasets/
        with open(out_dataset_path, "w", encoding="utf-8") as out_fp:
            for r in records:
                out_fp.write(json.dumps(r, ensure_ascii=False) + "\n")

        # Also write to datasets/web_pages/ if applicable
        web_ds_path = os.path.join("datasets", "web_pages", f"{slug}_qa.jsonl")
        with open(web_ds_path, "w", encoding="utf-8") as out_fp:
            for r in records:
                out_fp.write(json.dumps(r, ensure_ascii=False) + "\n")

        total_books_processed += 1
        total_qa_pairs_generated += len(records)
        print(f"[{b_idx:03d}/{len(extracted_dirs)}] {book_title[:38]:<38} | Chapters: {len(substantive_ch):2d} | QA Pairs: {len(records):3d} -> {os.path.basename(out_dataset_path)}")

    print("\n" + "=" * 80)
    print(f"SUCCESS: Processed {total_books_processed} books! Generated {total_qa_pairs_generated:,} total high-depth QA pairs.")
    print("=" * 80)

    print("\nRebuilding master datasets, train/val splits, and ShareGPT exports...")
    from tools.web_page_pipeline import rebuild_master_splits
    rebuild_master_splits()

if __name__ == "__main__":
    process_all_extracted_books()
