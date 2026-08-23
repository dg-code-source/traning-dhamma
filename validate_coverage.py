#!/usr/bin/env python3
"""
validate_coverage.py — Comprehensive Two-Layer Coverage & Gap Analysis Tool.
Layer 1: Chapter-level coverage against substantive book chapters.
Layer 2: Key Pāli term & concept coverage against source texts.
"""

import os
import sys
import json
import re
from collections import Counter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

EXTRACTED_DIR = "documents/extracted"
DATASETS_DIR = "datasets"
REPORT_JSON = "datasets/coverage_report.json"
REPORT_MD = "datasets/coverage_report.md"

SKIP_PATTERNS = [
    r"^copyright", r"^acknowledgement", r"^glossary", r"^preface",
    r"^contents", r"^abbreviation", r"^note to the reader",
    r"^further resource", r"^about the author", r"^foreword",
    r"^introduction$", r"^blank page", r"^selected chant",
    r"^appendix", r"^index", r"^bibliography", r"^dedication",
    r"^bio\.pdf", r"^cover", r"^title page",
]

PALI_TERMS = [
    "anicca", "dukkha", "anatta", "anattā", "tanha", "taṇhā",
    "sati", "samadhi", "samādhi", "panna", "paññā", "sila", "sīla",
    "metta", "mettā", "karuna", "karuṇā", "mudita", "muditā",
    "upekkha", "upekkhā", "nibbana", "nibbāna", "sankhara", "saṅkhāra",
    "vipassana", "vipassanā", "jhana", "jhāna", "kamma",
    "bhavana", "bhāvanā", "papanca", "papañca", "sunnata", "suññatā",
    "piti", "pīti", "sukha", "vedana", "vedanā", "samsara", "saṃsāra",
    "paticca samuppada", "paṭicca-samuppāda", "cetana", "cetanā",
    "avijja", "avijjā", "lobha", "dosa", "moha", "khanti",
    "nekkhamma", "adhitthana", "adhiṭṭhāna", "viriya",
    "sacca", "anapanasati", "ānāpānasati", "brahmavihara", "brahmavihāra",
    "kilesa", "vinaya", "dhamma", "sangha", "saṅgha", "buddha", "buddho",
    "nirodha", "magga", "samudaya", "raga", "rāga", "bhava",
    "upadana", "upādāna", "phassa", "nama-rupa", "nāma-rūpa",
    "ayatana", "āyatana", "khandha", "citta", "mano", "vinnana", "viññāṇa",
    "bojjhanga", "bojjhaṅga", "arahant", "bodhisatta",
    "dana", "dāna", "patimokkha", "pātimokkha",
    "nivarana", "nīvaraṇa", "kamacchanda", "kāmacchanda",
    "byapada", "byāpāda", "thina-middha", "uddhacca",
    "vicikiccha", "vicikicchā", "saddha", "saddhā",
    "mana", "māna", "avippatiisara", "avippaṭisāra",
    "ahankara", "ahaṅkāra", "maminkara", "mamiṅkāra",
    "atammayata", "atammayatā", "appamada", "appamāda",
]

CUSTOM_MAP = {
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
    "The Lesser, The Greater, The Diamond and The Way - Ajahn Amaro": "The_Lesser_The_Greater_The_Diamond_The_Way_qa.jsonl",
    "The Lesser, The Greater, The Diamond and The Way": "The_Lesser_The_Greater_The_Diamond_The_Way_qa.jsonl",
    "Serenity Is the Final Word": "Serenity_Is_the_Final_Word_qa.jsonl",
    "Small Boat, Great Mountain": "Small_Boat_Great_Mountain_qa.jsonl",
    "The Breakthrough": "The_Breakthrough_qa.jsonl",
    "Finding the Missing Peace": "Finding_the_Missing_Peace_qa.jsonl",
    "Inner Listening": "Inner_Listening_qa.jsonl",
    "Silent Rain": "Silent_Rain_qa.jsonl",
    "The Island": "The_Island_qa.jsonl",
    "Broad View, Boundless Heart": "Broad_View_Boundless_Heart_qa.jsonl",
    "Tudong, The Long Road North": "Tudong_The_Long_Road_North_qa.jsonl",
    "Don't Push": "Dont_Push_qa.jsonl",
    "I’m Right, You’re Wrong!": "Im_Right_Youre_Wrong_qa.jsonl",
    "I'm Right, You're Wrong!": "Im_Right_Youre_Wrong_qa.jsonl",
    "For the Love of the World": "For_the_Love_of_the_World_qa.jsonl",
    "Who Is Pulling The Strings": "Who_Is_Pulling_The_Strings_qa.jsonl",
    "Who Is Pulling The Strings?": "Who_Is_Pulling_The_Strings_qa.jsonl",
    "CatApo Web": "CatApo_qa.jsonl",
    "Fear and Fearlessness Web": "Fear_and_Fearlessness_qa.jsonl",
    "HEA 1 Reality Web": "HEA_1_Reality_qa.jsonl",
    "HEA 2 Emotion Web": "HEA_2_Emotion_qa.jsonl",
    "HEA 3 People Web": "HEA_3_People_qa.jsonl",
    "HEA 4 Money Web": "HEA_4_Money_qa.jsonl",
    "HEA 5 Beyond Web": "HEA_5_Beyond_qa.jsonl",
    "HEA Anthology Web": "HEA_Anthology_qa.jsonl",
    "Just One More": "Just_One_More_qa.jsonl",
    "Bio.pdf": "Less_Is_More_qa.jsonl",
    "Like a River - The life of a boy named Todd": "Like_a_River_qa.jsonl",
    "Mara Mangala web": "Mara_Mangala_qa.jsonl",
    "Mara and the Mangala II   Ajahn Amaro": "Mara_and_the_Mangala_II_qa.jsonl",
    "Mind Is What Matters NEW": "Mind_Is_What_Matters_qa.jsonl",
    "Rain on the Nile": "Rain_on_the_Nile_qa.jsonl",
    "Roots  Currents web": "Roots_and_Currents_qa.jsonl",
    "Rugged Interdependency": "Rugged_Interdependency_qa.jsonl",
    "The Dhamma and the Real World": "The_Dhamma_and_the_Real_World_qa.jsonl",
    "The Hush web": "The_Hush_qa.jsonl",
    "An Introduction to the Life and Teachings of Ajahn Chah": "Intro_Life_Teachings_Ajahn_Chah_qa.jsonl",
    "Still Flowing Water": None,
}

STOP_WORDS = {
    "the", "a", "an", "of", "in", "to", "and", "is", "it", "for", "with",
    "on", "at", "by", "from", "as", "or", "that", "this", "but", "be",
    "are", "was", "were", "been", "being", "have", "has", "had", "do",
    "does", "did", "not", "we", "you", "i", "he", "she", "they", "our",
    "your", "my", "their", "chapter", "part", "volume", "vol"
}

def is_substantive_chapter(title: str, word_count: int) -> bool:
    if word_count < 150:
        return False
    t_clean = title.strip().lower()
    for pat in SKIP_PATTERNS:
        if re.search(pat, t_clean):
            return False
    return True

def extract_title_keywords(title: str) -> set:
    t = re.sub(r"^(chapter|\d+|part|\s|[:.-])+", "", title, flags=re.IGNORECASE)
    words = re.findall(r"[a-zA-Z\u0100-\u024F]+", t.lower())
    return {w for w in words if len(w) > 2 and w not in STOP_WORDS}

def map_books():
    books = []
    if not os.path.exists(EXTRACTED_DIR):
        return books
    for b in sorted(os.listdir(EXTRACTED_DIR)):
        bp = os.path.join(EXTRACTED_DIR, b)
        if not os.path.isdir(bp):
            continue
        mp = os.path.join(bp, "metadata.json")
        if not os.path.exists(mp):
            continue
        with open(mp, "r", encoding="utf-8") as f:
            meta = json.load(f)
        title = meta.get("title", b)
        total_words = meta.get("total_words", 0)
        chapters = meta.get("chapters", [])
        
        ds_file = None
        if title in CUSTOM_MAP:
            ds_file = CUSTOM_MAP[title]
        else:
            clean_title = title.lower().replace("’", "").replace("'", "")
            for f in os.listdir(DATASETS_DIR):
                if f.endswith(".jsonl") and not f.startswith("master_") and f not in ("train.jsonl", "val.jsonl"):
                    clean_df = f.lower().replace("_", " ").replace(" qa.jsonl", "").replace(".jsonl", "")
                    if clean_df in clean_title or clean_title in clean_df:
                        ds_file = f
                        break
        
        ds_path = os.path.join(DATASETS_DIR, ds_file) if (ds_file and os.path.exists(os.path.join(DATASETS_DIR, ds_file))) else None
        
        books.append({
            "book_title": title,
            "book_dir": b,
            "total_words": total_words,
            "chapters": chapters,
            "dataset_file": ds_file,
            "dataset_path": ds_path
        })
    return books

def analyze_book(binfo):
    substantive_chs = [c for c in binfo["chapters"] if is_substantive_chapter(c.get("title", c.get("filename", "")), c.get("word_count", 0))]
    
    qa_text_blob = ""
    qa_pairs = []
    if binfo["dataset_path"] and os.path.exists(binfo["dataset_path"]):
        with open(binfo["dataset_path"], "r", encoding="utf-8-sig") as f:
            for line in f:
                if not line.strip(): continue
                r = json.loads(line)
                q = r["messages"][1]["content"]
                a = r["messages"][2]["content"]
                qa_pairs.append((q, a))
                qa_text_blob += f" {q} {a} "
    
    qa_text_lower = qa_text_blob.lower()
    
    # Layer 1: Chapter coverage
    covered_chs = []
    uncovered_chs = []
    for ch in substantive_chs:
        ch_title = ch.get("title", ch.get("filename", ""))
        keywords = extract_title_keywords(ch_title)
        if not keywords:
            # Short generic title, fallback to checking if any keyword matches
            covered_chs.append(ch_title)
            continue
        matched_kw = [kw for kw in keywords if kw in qa_text_lower]
        coverage_ratio = len(matched_kw) / len(keywords)
        if coverage_ratio >= 0.4:
            covered_chs.append(ch_title)
        else:
            uncovered_chs.append({
                "title": ch_title,
                "word_count": ch.get("word_count", 0),
                "file": ch.get("file", ch.get("filename", ""))
            })
            
    ch_cov_pct = (len(covered_chs) / len(substantive_chs) * 100) if substantive_chs else 100.0
    
    # Layer 2: Pali concept coverage
    full_book_path = os.path.join(EXTRACTED_DIR, binfo["book_dir"], "full_book.txt")
    source_pali_counts = {}
    if os.path.exists(full_book_path):
        with open(full_book_path, "r", encoding="utf-8", errors="ignore") as f:
            src_text = f.read().lower()
        for term in PALI_TERMS:
            c = src_text.count(term)
            if c >= 3:
                source_pali_counts[term] = c
                
    sig_pali = list(source_pali_counts.keys())
    pali_covered = [p for p in sig_pali if p in qa_text_lower]
    pali_missing = [p for p in sig_pali if p not in qa_text_lower]
    pali_cov_pct = (len(pali_covered) / len(sig_pali) * 100) if sig_pali else 100.0
    
    status = "MISSING_QA" if not binfo["dataset_path"] else ("HEALTHY" if ch_cov_pct >= 60 and pali_cov_pct >= 60 else "NEEDS_COVERAGE")
    
    return {
        "book_title": binfo["book_title"],
        "book_dir": binfo["book_dir"],
        "total_words": binfo["total_words"],
        "dataset_file": binfo["dataset_file"],
        "qa_count": len(qa_pairs),
        "status": status,
        "substantive_chapters_count": len(substantive_chs),
        "covered_chapters_count": len(covered_chs),
        "uncovered_chapters_count": len(uncovered_chs),
        "chapter_coverage_pct": round(ch_cov_pct, 1),
        "covered_chapters": covered_chs,
        "uncovered_chapters": uncovered_chs,
        "significant_pali_count": len(sig_pali),
        "covered_pali_count": len(pali_covered),
        "missing_pali_count": len(pali_missing),
        "pali_coverage_pct": round(pali_cov_pct, 1),
        "missing_pali_terms": pali_missing
    }

def main():
    books = map_books()
    results = [analyze_book(b) for b in books]
    
    os.makedirs(os.path.dirname(REPORT_JSON), exist_ok=True)
    with open(REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    # Generate Markdown Report
    lines = [
        "# Dhamma Corpus Comprehensive Coverage & Gap Analysis Report",
        "",
        f"Total Extracted Books Audited: **{len(results)}**",
        "",
        "## 1. Overall Summary Table",
        "",
        "| Book Title | Words | QA Pairs | Substantive Chs | Ch Cov % | Pali Cov % | Status |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: |"
    ]
    
    healthy_count = sum(1 for r in results if r["status"] == "HEALTHY")
    needs_cov = sum(1 for r in results if r["status"] == "NEEDS_COVERAGE")
    missing_qa = sum(1 for r in results if r["status"] == "MISSING_QA")
    
    for r in results:
        lines.append(f"| {r['book_title'][:40]} | {r['total_words']:,} | {r['qa_count']} | {r['substantive_chapters_count']} | {r['chapter_coverage_pct']}% | {r['pali_coverage_pct']}% | `{r['status']}` |")
        
    lines.extend([
        "",
        "## 2. Status Breakdown",
        f"- **Healthy Coverage**: {healthy_count} books",
        f"- **Needs Coverage (Gaps Identified)**: {needs_cov} books",
        f"- **Missing Dataset**: {missing_qa} books",
        "",
        "## 3. Detailed Gaps Per Book",
        ""
    ])
    
    for r in results:
        if r["status"] != "HEALTHY":
            lines.append(f"### {r['book_title']} (`{r['status']}`)")
            lines.append(f"- **Target Dataset**: `{r['dataset_file']}`")
            lines.append(f"- **Total Words**: {r['total_words']:,} | **Current QA Pairs**: {r['qa_count']}")
            if r["uncovered_chapters"]:
                lines.append(f"- **Uncovered Chapters ({len(r['uncovered_chapters'])}):**")
                for uc in r["uncovered_chapters"][:10]:
                    lines.append(f"  - *{uc['title']}* ({uc['word_count']} words)")
                if len(r["uncovered_chapters"]) > 10:
                    lines.append(f"  - ... and {len(r['uncovered_chapters'])-10} more")
            if r["missing_pali_terms"]:
                lines.append(f"- **Missing Pāli Concepts:** {', '.join(r['missing_pali_terms'][:12])}")
            lines.append("")
            
    with open(REPORT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        
    print(f"[Done] Analyzed {len(results)} books.")
    print(f"       Healthy: {healthy_count} | Needs Coverage: {needs_cov} | Missing QA: {missing_qa}")
    print(f"       Saved JSON: {REPORT_JSON}")
    print(f"       Saved MD:   {REPORT_MD}")

if __name__ == "__main__":
    main()
