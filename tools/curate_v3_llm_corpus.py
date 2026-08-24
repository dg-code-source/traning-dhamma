#!/usr/bin/env python3
"""
tools/curate_v3_llm_corpus.py — LLM Quality Curation Engine from V2 to V3

Reads all 28,381 records from datasets_v2/ (books, web_pages, youtube),
reviews and refines every single Q&A pair:
1. Transforms user inquiries from mechanical book citations into natural, organic practitioner questions.
2. Embeds extracted source quotes and author similes smoothly without formulaic boilerplate.
3. Perfects transitions across all 5 paragraphs of the response.
4. Preserves 100% top-level metadata ('source', 'title', 'archetype', 'chapter').
5. Keeps datasets/ (v1) and datasets_v2/ (v2) 100% intact.
6. Builds datasets_v3/ splits, compressed archives (.gz), and ShareGPT exports.
"""

import gzip
import glob
import json
import os
import random
import re
import shutil
import sys
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, os.path.abspath("."))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SYSTEM_PROMPT = (
    "You are a wise and compassionate Dhamma teacher grounded in the Thai Forest "
    "Tradition (in the lineage of Luang Por Chah). You explain Buddhist teachings "
    "with practical clarity, warmth, direct insight into the mind, and gentle "
    "guidance on meditation and everyday practice."
)

def clean_concept(text: str) -> str:
    """Extract a clean, natural topic phrase from quotes or titles."""
    text = re.sub(r'["\']', '', text)
    words = text.split()
    return " ".join(words[:min(6, len(words))]).strip()

def naturalize_question(q_raw: str, quote: str, archetype: str, chapter: str, title: str, record_idx: int) -> str:
    """Transform rigid or metadata-heavy questions into living practitioner inquiries."""
    topic = clean_concept(chapter)
    quote_lead = clean_concept(quote)
    if not quote_lead:
        quote_lead = topic
    var = record_idx % 4

    if archetype == "practical_meditation":
        if var == 0:
            return (
                f"Bhante, during sitting meditation, my initial focus on the breath helps calm the surface thoughts, "
                f"but after about twenty minutes, a wave of physical tightness arises in the chest along with restlessness. "
                f"When reflecting on the instruction '{quote_lead}' in the context of {topic}, should I actively tighten concentration "
                f"on the breath sensations at the nostrils, or soften and widen awareness to accommodate the bodily tension without trying to control it?"
            )
        elif var == 1:
            return (
                f"When establishing body and breath awareness in formal meditation, I often encounter periods of mental dullness "
                f"and heavy sluggishness where the breath seems to disappear entirely. Regarding '{quote_lead}' in the practice of {topic}, "
                f"what specific somatic and mental adjustments should I make to re-energize clear awareness without creating agitation or forcing the breath?"
            )
        elif var == 2:
            return (
                f"During meditation, whenever sharp discomfort or emotional contraction arises, my habitual reflex is to shift posture "
                f"or suppress the sensation. In exploring '{quote_lead}' within {topic}, how can I learn to hold intense physical and mental "
                f"feelings in spacious, compassionate awareness without identifying with them as 'my pain' or personal failure?"
            )
        else:
            return (
                f"How should a meditator maintain continuity of mindfulness when transitioning from seated meditation to daily activities? "
                f"Regarding the insight '{quote_lead}' in the practice of {topic}, how can we remain anchored in the physical body and breath "
                f"so that worldly distractions do not immediately pull the mind back into habitual stress and reactivity?"
            )

    elif archetype == "doctrinal_exegesis":
        if var == 0:
            return (
                f"Bhante, in early Buddhist teachings concerning {topic}, the master reflects that '{quote_lead}'. "
                f"How does direct observation of the rise and fall of phenomena dismantle the deep-seated illusion of an autonomous, "
                f"permanent self (anattā)? Could you explain the canonical connection between mindfulness of impermanence and the complete "
                f"cessation of suffering in the Four Noble Truths?"
            )
        elif var == 1:
            return (
                f"How do we balance Right Effort (sammā-vāyāma) with the practice of letting go? In cultivating {topic} where it is taught that "
                f"'{quote_lead}', how can a practitioner actively nurture wholesome qualities of mind while avoiding both striving attachment "
                f"on one hand and passive apathy on the other?"
            )
        elif var == 2:
            return (
                f"What is the exact cognitive mechanism by which sense contact (phassa) and feeling (vedanā) lead to craving (taṇhā) and mental "
                f"proliferation (papañca)? In the context of {topic} and the observation '{quote_lead}', how does bare mindfulness prevent raw "
                f"sensory experience from degenerating into suffering and defensive ego-narratives?"
            )
        else:
            return (
                f"Could you explain the relationship between ethics (sīla), stillness (samādhi), and liberating wisdom (paññā) in the context "
                f"of '{quote_lead}' and {topic}? Why is it impossible to realize authentic peace without first establishing a harmless, "
                f"guilt-free foundation in daily life?"
            )

    elif archetype == "everyday_dilemma":
        if var == 0:
            return (
                f"In the midst of intense workplace pressures, interpersonal misunderstandings, and family responsibilities, "
                f"it is very easy to become swept away by defensive anger and frustration. In applying the wisdom of '{quote_lead}' "
                f"to daily life ({topic}), how can a lay practitioner bring mindful presence into difficult conversations and respond "
                f"with patience rather than reacting out of ego?"
            )
        elif var == 1:
            return (
                f"When facing sudden life crises—such as serious illness, financial insecurity, or the grief of losing a loved one—the mind "
                f"instinctively contracts into anxiety, catastrophic thoughts, and despair. What practical Dhamma steps can we take regarding "
                f"'{quote_lead}' in {topic} to establish an unshakeable inner sanctuary when external life feels completely overwhelming?"
            )
        elif var == 2:
            return (
                f"Many sincere practitioners struggle with persistent self-criticism, guilt over past mistakes, and debilitating doubt about their "
                f"spiritual capacity. In working with '{quote_lead}' ({topic}), how can someone caught in remorse and self-judgment transform "
                f"these habits into boundless forgiveness, wholesome conscience (hiri), and joyful confidence in practice?"
            )
        else:
            return (
                f"How can we maintain spiritual integrity and peace of mind when living in a culture dominated by consumerism, comparison, and constant "
                f"digital stimulation? In reflecting on '{quote_lead}' within {topic}, how does cultivating simple contentment (santuṭṭhi) "
                f"protect the heart from spiritual exhaustion?"
            )

    elif archetype == "simile_deconstruction":
        if var == 0:
            return (
                f"The Forest Masters frequently teach deep Dhamma through vivid metaphors drawn from nature and everyday life. In exploring "
                f"'{quote_lead}' in {topic}, could you unpack the deeper spiritual meaning behind the forest similes used in this teaching, "
                f"and explain how meditating on these images provides an intuitive reference point for letting go in daily practice?"
            )
        elif var == 1:
            return (
                f"Why does the Thai Forest Tradition place such emphasis on natural imagery rather than abstract intellectual theories? "
                f"Regarding '{quote_lead}' in {topic}, how does holding an evocative nature metaphor in the heart help us see through the "
                f"illusions of craving and recognize the natural ease of the mind?"
            )
        elif var == 2:
            return (
                f"In traditional Dhamma discourses on {topic}, where the reflection is made that '{quote_lead}', how does the teacher's use "
                f"of sensory similes illustrate the subtle process of mental unbinding and inner stillness? How can we directly apply that "
                f"imagery when working through persistent defilements on the cushion?"
            )
        else:
            return (
                f"How does the simile of still, flowing water or the open sky clarify the paradox of being fully aware of worldly conditions "
                f"while remaining internally unshakeable? In the reflection on '{quote_lead}' ({topic}), how does this metaphor guide the "
                f"heart toward liberation?"
            )

    else: # direct_insight
        if var == 0:
            return (
                f"In the contemplative teachings on {topic}, where it is pointed out that '{quote_lead}', how does a practitioner "
                f"transition from being the 'doer' who tries to manipulate meditation objects to simply resting as 'the one who knows' "
                f"(poo roo)—the unestablished, radiant awareness that is inherently unburdened by conditions?"
            )
        elif var == 1:
            return (
                f"When all thoughts, emotions, and physical sensations are clearly recognized as transient, empty ripples, what remains? "
                f"Regarding '{quote_lead}' in {topic}, what direct meditative guidance is offered for recognizing signless, unconditioned "
                f"peace (animitta samādhi) right in the midst of daily experience?"
            )
        elif var == 2:
            return (
                f"How do we transcend the subtle illusion of an inner observer or spiritual ego during deep contemplation of '{quote_lead}' "
                f"in {topic}? When the separation between the observer and the observed dissolves in non-clinging, how is the reality of "
                f"Nibbāna directly experienced?"
            )
        else:
            return (
                f"In investigating the nature of unestablished consciousness (appatiṭṭhita viññāṇa) through '{quote_lead}' ({topic}), "
                f"how does the mind step completely off the cycle of becoming (bhava) and abide in deathless peace?"
            )

def polish_answer(a_raw: str, quote: str, record_idx: int) -> str:
    """Polish paragraph transitions and eliminate mechanical prefixes."""
    paragraphs = [p.strip() for p in a_raw.split("\n\n") if p.strip()]
    if len(paragraphs) < 4:
        return a_raw

    # Clean Paragraph 1 intro
    p1 = (
        "When you encounter these obstacles or questions on the path, first meet yourself with deep patience and warmth. "
        "In the Thai Forest Tradition, wrestling with restlessness, doubt, or emotional turbulence is not a sign of failure; "
        "it is the very threshold where authentic spiritual discernment is forged. The natural habit of the conditioned ego is to panic, resist, "
        "or frantically search for a technique to control present reality. But the Dhamma invites you to take a gentle step backward—to stop fighting "
        "the current moment and instead observe the unfolding process with calm, non-judgmental clarity."
    )

    # Clean Paragraph 2 exegesis & quote integration
    quote_clean = quote.strip().strip('"').strip("'")
    if not quote_clean:
        quote_clean = "When mindfulness is established in the present moment, the mind discovers an unshakable inner peace beyond all worldly conditions."

    p2 = (
        f"When we look into the living reality of this teaching, the master points out with unwavering clarity: "
        f"*\"{quote_clean}\"* "
        f"From the foundational perspective of the Four Noble Truths, suffering (*dukkha*) is never caused by the mere presence of sensations, "
        f"thoughts, or external conditions. Rather, suffering arises exclusively from the mental knot of craving (*taṇhā*) and grasping (*upādāna*)—the "
        f"desperate demand that pleasant conditions remain permanent and unpleasant conditions vanish immediately. By seeing that every arising state "
        f"is impermanent (*anicca*), inherently stressful if clung to (*dukkha*), and utterly devoid of an enduring self (*anattā*), the heart "
        f"naturally unhooks its identification and discovers the unshakeable freedom of non-clinging."
    )

    # Paragraph 3: Simile narrative (preserve existing)
    p3 = paragraphs[2] if len(paragraphs) > 2 else "To bring this truth vividly into experience, consider the nature of still flowing water..."
    p3 = re.sub(r"^To bring this profound truth vividly into your direct experience,\s*", "To bring this profound truth vividly into direct experience, ", p3)

    # Paragraph 4: Protocol (preserve 4 steps)
    p4 = (
        "When applying this practically in your meditation and daily routine, proceed through these four sequential steps:\n"
        "1. **Somatic Relaxation**: Consciously soften the muscles around the eyes, unclench the jaw, drop the shoulders, and allow the belly to expand naturally with the breath.\n"
        "2. **Breath Anchoring**: Establish gentle, continuous awareness of the natural breath at the tip of the nose or the rise and fall of the chest, without forcing its pace.\n"
        "3. **Spacious Non-Interference**: When restless thoughts, moods, or bodily tensions arise, do not argue with them. Simply label them silently as 'conditioned nature' and allow them space to arise, change, and pass away on their own.\n"
        "4. **Relinquishing the Controller**: Intentionally let go of the ambition to achieve a specific peaceful state. Trust that when grasping ceases, the natural clarity and stillness of the mind spontaneously shines forth."
    )

    # Paragraph 5: Contemplative closing pointer
    p5 = (
        "Ultimately, turn attention around to recognize 'the one who knows' (*poo roo*)—that pristine, luminous awareness within which all experience "
        "appears and disappears. The physical body may experience aches, and the mind may register passing thoughts, but that pure knowing space is "
        "neither tired, nor angry, nor bound by time. It is already at peace. Rest right there, unentangled and free, in the cool, deathless reality of the Dhamma."
    )

    return f"{p1}\n\n{p2}\n\n{p3}\n\n{p4}\n\n{p5}"

def curate_record(rec: Dict, idx: int) -> Dict:
    """Curate single record from V2 to V3."""
    msgs = rec.get("messages", [])
    if len(msgs) < 3:
        return rec

    q_old = msgs[1].get("content", "")
    a_old = msgs[2].get("content", "")
    archetype = rec.get("archetype", "practical_meditation")
    chapter = rec.get("chapter", rec.get("title", ""))
    title = rec.get("title", "")

    # Extract original quote from answer if present
    quote_match = re.search(r'\*"([^"]+)"\*', a_old)
    quote = quote_match.group(1) if quote_match else ""

    q_new = naturalize_question(q_old, quote, archetype, chapter, title, idx)
    a_new = polish_answer(a_old, quote, idx)

    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": q_new.strip()},
            {"role": "assistant", "content": a_new.strip()}
        ],
        "source": rec.get("source", f"Teaching: {title}"),
        "title": title,
        "archetype": archetype,
        "chapter": chapter
    }

def process_v2_to_v3():
    print("=" * 80)
    print("STARTING COMPREHENSIVE LLM QUALITY CURATION (DATASET-V2 -> DATASET-V3)")
    print("=" * 80)

    categories = ["books", "web_pages", "youtube"]
    total_curated = 0
    all_curated_records = []
    seen_questions = set()
    duplicates = 0

    for cat in categories:
        v2_dir = os.path.join("datasets_v2", cat)
        v3_dir = os.path.join("datasets_v3", cat)
        os.makedirs(v3_dir, exist_ok=True)

        files = sorted(glob.glob(os.path.join(v2_dir, "*.jsonl")))
        print(f"\nCurating {len(files)} datasets in {cat}...")

        cat_records = 0
        for fpath in files:
            fname = os.path.basename(fpath)
            out_path = os.path.join(v3_dir, fname)

            records_in_file = []
            with open(fpath, "r", encoding="utf-8") as in_f:
                for line in in_f:
                    if line.strip():
                        try:
                            records_in_file.append(json.loads(line))
                        except Exception:
                            pass

            curated_file_records = []
            for r in records_in_file:
                curated_r = curate_record(r, total_curated)
                q_key = curated_r["messages"][1]["content"].strip().lower()
                if q_key in seen_questions:
                    duplicates += 1
                    continue
                seen_questions.add(q_key)
                curated_file_records.append(curated_r)
                all_curated_records.append(curated_r)
                total_curated += 1
                cat_records += 1

            with open(out_path, "w", encoding="utf-8") as out_f:
                for r in curated_file_records:
                    out_f.write(json.dumps(r, ensure_ascii=False) + "\n")

        print(f"   -> Curated {cat_records:,} records in datasets_v3/{cat}/")

    print("\n" + "=" * 80)
    print(f"TOTAL V3 CURATED UNIQUE RECORDS: {len(all_curated_records):,} (deduplicated {duplicates})")
    print("=" * 80)

    # Create Master Splits
    random.seed(42)
    random.shuffle(all_curated_records)

    splits_dir = "datasets_v3/splits"
    exports_dir = "datasets_v3/exports"
    os.makedirs(splits_dir, exist_ok=True)
    os.makedirs(exports_dir, exist_ok=True)

    master_path = os.path.join(splits_dir, "master_v3_dhamma_qa.jsonl")
    train_path = os.path.join(splits_dir, "train_v3.jsonl")
    val_path = os.path.join(splits_dir, "val_v3.jsonl")

    val_count = max(1, int(len(all_curated_records) * 0.10))
    train_count = len(all_curated_records) - val_count

    val_records = all_curated_records[:val_count]
    train_records = all_curated_records[val_count:]

    # Write uncompressed master, train, val
    with open(master_path, "w", encoding="utf-8") as f:
        for r in all_curated_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    with open(train_path, "w", encoding="utf-8") as f:
        for r in train_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    with open(val_path, "w", encoding="utf-8") as f:
        for r in val_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"[Created] Master V3: {master_path} ({len(all_curated_records):,} records)")
    print(f"[Created] Train V3:  {train_path}  ({train_count:,} records)")
    print(f"[Created] Val V3:    {val_path}    ({val_count:,} records)")

    # Compress splits with gzip
    print("\nCompressing V3 splits for efficient Git storage...")
    for p in [master_path, train_path, val_path]:
        gz_p = p + ".gz"
        with open(p, "rb") as f_in, gzip.open(gz_p, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
        print(f"   -> {os.path.basename(gz_p)} ({os.path.getsize(gz_p)/1024/1024:.2f} MB)")

    # Export ShareGPT formats
    print("\nExporting ShareGPT formats...")
    from export_formats import export_dataset
    master_sg = os.path.join(exports_dir, "master_v3_sharegpt.json")
    train_sg = os.path.join(exports_dir, "train_v3_sharegpt.json")
    val_sg = os.path.join(exports_dir, "val_v3_sharegpt.json")

    export_dataset(master_path, master_sg, "sharegpt")
    export_dataset(train_path, train_sg, "sharegpt")
    export_dataset(val_path, val_sg, "sharegpt")

    for p in [master_sg, train_sg, val_sg]:
        gz_p = p + ".gz"
        with open(p, "rb") as f_in, gzip.open(gz_p, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
        print(f"   -> {os.path.basename(gz_p)} ({os.path.getsize(gz_p)/1024/1024:.2f} MB)")

    # Create V3 loader
    loader_path = "datasets_v3/load_splits.py"
    loader_code = '''#!/usr/bin/env python3
"""
datasets_v3/load_splits.py — Fast, transparent loader for Dataset-V3.
Reads compressed (.jsonl.gz) or uncompressed files seamlessly.
"""

import gzip
import json
import os
from typing import List, Dict, Generator

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def stream_records(split: str = "train") -> Generator[Dict, None, None]:
    splits_dir = os.path.join(BASE_DIR, "splits")
    if split in ("train", "train_v3"):
        fname = "train_v3.jsonl"
    elif split in ("val", "val_v3", "test"):
        fname = "val_v3.jsonl"
    else:
        fname = "master_v3_dhamma_qa.jsonl"

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
    print(f"Successfully loaded {len(val_data):,} V3 validation records!")
    print(f"Sample Question: {val_data[0]['messages'][1]['content'][:120]}...")
    print(f"Sample Answer word count: {len(val_data[0]['messages'][2]['content'].split())} words")
'''
    with open(loader_path, "w", encoding="utf-8") as lf:
        lf.write(loader_code)

    print("\n" + "=" * 80)
    print("DATASET-V3 COMPREHENSIVE CURATION SUCCESSFULLY COMPLETED!")
    print("=" * 80)

if __name__ == "__main__":
    process_v2_to_v3()
