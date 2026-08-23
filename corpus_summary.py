import json
import os
import sys
from typing import Dict, List


def analyze_jsonl(file_path: str) -> Dict:
    """Extract statistics from a single JSONL file."""
    total_records = 0
    user_words = []
    assistant_words = []

    with open(file_path, "r", encoding="utf-8-sig") as f:
        for line in f:
            line_str = line.strip()
            if not line_str:
                continue
            try:
                rec = json.loads(line_str)
                messages = rec.get("messages", [])
                if len(messages) >= 3:
                    u_text = messages[1].get("content", "")
                    a_text = messages[2].get("content", "")
                    user_words.append(len(u_text.split()))
                    assistant_words.append(len(a_text.split()))
                    total_records += 1
            except json.JSONDecodeError:
                continue

    return {
        "file": os.path.basename(file_path),
        "path": file_path,
        "count": total_records,
        "avg_user_words": sum(user_words) / len(user_words) if user_words else 0,
        "avg_assistant_words": sum(assistant_words) / len(assistant_words) if assistant_words else 0,
        "total_assistant_words": sum(assistant_words),
    }


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    root_dir = os.path.abspath(os.path.dirname(__file__))
    datasets_dir = os.path.join(root_dir, "datasets")
    transcripts_dir = os.path.join(root_dir, "transcripts")
    extracted_dir = os.path.join(root_dir, "documents", "extracted")

    print("\n" + "=" * 80)
    print("                      DHAMMA QA CORPUS INVENTORY & STATUS")
    print("=" * 80)

    # 1. Dataset statistics
    dataset_files = []
    if os.path.exists(datasets_dir):
        for f in sorted(os.listdir(datasets_dir)):
            if f.endswith(".jsonl") and not f.startswith("master_") and f not in ("train.jsonl", "val.jsonl"):
                dataset_files.append(os.path.join(datasets_dir, f))

    stats_list = [analyze_jsonl(fp) for fp in dataset_files]
    total_qa = sum(s["count"] for s in stats_list)
    total_words = sum(s["total_assistant_words"] for s in stats_list)

    print(f"\n[Generated Datasets ({len(stats_list)} files)]")
    print(f"{'Dataset Name':<50} | {'QA Pairs':<8} | {'Avg Words':<10}")
    print("-" * 75)
    for s in stats_list:
        print(f"{s['file'][:48]:<50} | {s['count']:<8} | {s['avg_assistant_words']:<10.0f}")
    print("-" * 75)
    print(f"{'TOTAL CORPUS':<50} | {total_qa:<8} | {total_words / total_qa if total_qa else 0:<10.0f}")
    print(f"Total assistant training words: {total_words:,} words (~{int(total_words * 1.35):,} tokens)")

    # 2. Extracted Books Inventory
    print("\n" + "-" * 80)
    print("[Extracted Books (EPUB / PDF)]")
    book_meta_list = []
    if os.path.exists(extracted_dir):
        books = sorted(os.listdir(extracted_dir))
        for b in books:
            b_path = os.path.join(extracted_dir, b)
            if os.path.isdir(b_path):
                meta_file = os.path.join(b_path, "metadata.json")
                if os.path.exists(meta_file):
                    with open(meta_file, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    title = meta.get('title', b).replace('’', "'").replace('‘', "'")
                    author = meta.get('author', 'Unknown').replace('’', "'").replace('‘', "'")
                    w_count = meta.get('total_words', 0)
                    ch_count = meta.get('total_chapters', 0)
                    book_meta_list.append({"name": b, "title": title, "author": author, "words": w_count, "chapters": ch_count})
                    print(f" - {title} ({author}) - {w_count:,} words, {ch_count} chapters")
                else:
                    print(f" - {b} (Extracted)")
    else:
        print(" (None)")

    # 3. YouTube Transcripts Inventory
    print("\n" + "-" * 80)
    print("[Extracted YouTube Transcripts]")
    transcript_list = []
    if os.path.exists(transcripts_dir):
        transcripts = [f for f in sorted(os.listdir(transcripts_dir)) if f.endswith(".txt")]
        for t in transcripts:
            t_path = os.path.join(transcripts_dir, t)
            with open(t_path, "r", encoding="utf-8", errors="ignore") as f:
                w_count = len(f.read().split())
            name = t[:-4]
            transcript_list.append({"name": name, "words": w_count})
            print(f" - {name} ({w_count:,} words)")
    else:
        print(" (None)")

    # 4. Quality & Coverage Health Audit
    print("\n" + "-" * 80)
    print("[Source-to-Dataset Quality & Coverage Health]")
    print(f"{'Source Title / Subject':<45} | {'Source Words':<12} | {'QA Pairs':<8} | {'Avg Words':<9} | {'Health Status'}")
    print("-" * 95)

    dataset_map = {s["file"]: s for s in stats_list}

    # Direct filename mapping overrides if title differs from dataset filename
    custom_map = {
        "SiTTL_Cover-B": "Seen_in_Their_True_Light_qa.jsonl",
        "Stillness Flowing": "Stillness_Flowing_qa.jsonl",
        "The Contemplative's Craft": "The_Contemplatives_Craft_qa.jsonl",
        "The contemplative's companion": "The_Contemplatives_Companion_qa.jsonl",
        "The Stillness of Being": "The_Stillness_of_Being_qa.jsonl",
        "Daughters & Sons": "Daughters_and_Sons_qa.jsonl",
        "Mindfulness, Precepts and Crashing in the Same Car": "Mindfulness_Precepts_and_Crashing_in_the_Same_Car_qa.jsonl",
        "without and within": "Without_and_Within_qa.jsonl",
        "Aj Jaya The Real Practice": "The_Real_Practice_qa.jsonl",
        "In Simple Terms: 108 Dhamma Similes": "In_Simple_Terms_Similes_qa.jsonl",
        "It's Like This: 108 Dhamma Similes": "Its_Like_This_108_Dhamma_Similes_qa.jsonl",
        "The Collected Teachings of Ajahn Chah - Single Volume": "The_Collected_Teachings_of_Ajahn_Chah_qa.jsonl",
        "Ajahn Sumedho Volume 1 - Peace is a Simple Step": "Peace_is_a_Simple_Step_qa.jsonl",
        "Ajahn Sumedho Volume 3 - Direct Realization": "Direct_Realization_qa.jsonl",
        "Ajahn Sumedho Volume 5 - The Wheel of Truth": "The_Wheel_of_Truth_qa.jsonl",
        "Cittaviveka": "Cittaviveka_qa.jsonl",
        "Intuitive Awareness": "Intuitive_Awareness_qa.jsonl",
        "Mindfulness: The Path to the Deathless": "Mindfulness_The_Path_to_the_Deathless_qa.jsonl",
        "Now is the Knowing": "Now_is_the_Knowing_qa.jsonl",
        "On Love": "On_Love_qa.jsonl",
        "Teachings From the Forest": "Teachings_From_the_Forest_qa.jsonl",
        "The Four Noble Truths": "The_Four_Noble_Truths_qa.jsonl",
        "Gratitude-Book-AW2-singles": "Gratitude_qa.jsonl",
        "The Way it is.indd": "The_Way_It_Is_qa.jsonl",
        "true but not right": "True_But_Not_Right_qa.jsonl",
        "Fear": "Fear_Buddhadasa_Bhikkhu_qa.jsonl",
        "Buddhadāsa Indapañño Archives": "Fear_Buddhadasa_Bhikkhu_qa.jsonl",
        "Blank Page": "Its_Like_This_108_Dhamma_Similes_qa.jsonl",
        "A Dhammapada for Contemplation": "A_Dhammapada_for_Contemplation_qa.jsonl",
        "Dhammapada Reflections Volume One": "Dhammapada_Reflections_Vol1_qa.jsonl",
        "Dhammapada Reflections Volume 2": "Dhammapada_Reflections_Vol2_qa.jsonl",
        "Dhammapada Reflections Volume Three": "Dhammapada_Reflections_Vol3_qa.jsonl",
        "Alert to the Needs of the Journey": "Alert_to_the_Needs_of_the_Journey_qa.jsonl",
        "In Any Given Moment": "In_Any_Given_Moment_qa.jsonl",
        "Sanity in the Midst of Uncertainty": "Sanity_in_the_Midst_of_Uncertainty_qa.jsonl",
        "Servant of Reality": "Servant_of_Reality_qa.jsonl",
        "Sitting in the Buddhas Waiting Room": "Sitting_in_the_Buddhas_Waiting_Room_qa.jsonl",
        "Sitting in the Buddha's Waiting Room": "Sitting_in_the_Buddhas_Waiting_Room_qa.jsonl",
        "We Are All Translators": "We_Are_All_Translators_qa.jsonl",
        "Still Flowing Water": None,  # Micro extract (136 words)
    }

    # Match books to datasets
    for bm in book_meta_list:
        matched_ds = None
        b_title = bm["title"]
        if b_title in custom_map:
            ds_name = custom_map[b_title]
            matched_ds = dataset_map.get(ds_name) if ds_name else None
        else:
            for df, s in dataset_map.items():
                clean_df = df.lower().replace("_", " ").replace(" qa.jsonl", "").replace(".jsonl", "")
                clean_bm = b_title.lower().replace("’", "").replace("'", "")
                if clean_bm == clean_df or clean_df in clean_bm:
                    matched_ds = s
                    break

        if matched_ds:
            qa_count = matched_ds["count"]
            avg_w = matched_ds["avg_assistant_words"]
            if bm["words"] > 50000 and qa_count < 35:
                status = "[NEEDS DEPTH]"
            elif avg_w < 75:
                status = "[ANSWERS BRIEF]"
            else:
                status = "[HEALTHY]"
            print(f"{b_title[:43]:<45} | {bm['words']:<12,} | {qa_count:<8} | {avg_w:<9.0f} | {status}")
        else:
            if b_title == "Still Flowing Water":
                print(f"{b_title[:43]:<45} | {bm['words']:<12,} | {'-':<8} | {'-':<9} | [INCLUDED IN SF]")
            else:
                print(f"{b_title[:43]:<45} | {bm['words']:<12,} | {'-':<8} | {'-':<9} | [MISSING QA]")

    for tm in transcript_list:
        matched_ds = None
        t_name = tm["name"]
        for df, s in dataset_map.items():
            clean_df = df.lower().replace("_", " ").replace(" qa.jsonl", "").replace(".jsonl", "")
            clean_tm = t_name.lower().replace("_", " ")
            if clean_tm == clean_df or clean_df in clean_tm:
                matched_ds = s
                break
        if matched_ds:
            qa_count = matched_ds["count"]
            avg_w = matched_ds["avg_assistant_words"]
            status = "[HEALTHY]" if qa_count >= 15 and avg_w >= 80 else "[NEEDS DEPTH]"
            print(f"{t_name[:43]:<45} | {tm['words']:<12,} | {qa_count:<8} | {avg_w:<9.0f} | {status}")
        else:
            print(f"{t_name[:43]:<45} | {tm['words']:<12,} | {'-':<8} | {'-':<9} | [MISSING QA]")

    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
