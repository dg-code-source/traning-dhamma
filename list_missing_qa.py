#!/usr/bin/env python3
"""list_missing_qa.py - List all extracted books > 10k words with no matching dataset."""
import os, json, sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ED = "documents/extracted"
DD = "datasets"

CUSTOM_MAP_TITLES = {
    "SiTTL_Cover-B", "Stillness Flowing", "The Contemplative's Craft",
    "The contemplative's companion", "The Stillness of Being", "Daughters & Sons",
    "Mindfulness, Precepts and Crashing in the Same Car", "without and within",
    "Aj Jaya The Real Practice", "In Simple Terms: 108 Dhamma Similes",
    "It's Like This: 108 Dhamma Similes",
    "The Collected Teachings of Ajahn Chah - Single Volume",
    "Ajahn Sumedho Volume 1 - Peace is a Simple Step",
    "Ajahn Sumedho Volume 3 - Direct Realization",
    "Ajahn Sumedho Volume 5 - The Wheel of Truth",
    "Cittaviveka", "Intuitive Awareness",
    "Mindfulness: The Path to the Deathless", "Now is the Knowing", "On Love",
    "Teachings From the Forest", "The Four Noble Truths",
    "Gratitude-Book-AW2-singles", "The Way it is.indd", "true but not right",
    "Fear", "A Dhammapada for Contemplation",
    "Dhammapada Reflections Volume One", "Dhammapada Reflections Volume 2",
    "Dhammapada Reflections Volume Three", "Alert to the Needs of the Journey",
    "In Any Given Moment", "Sanity in the Midst of Uncertainty",
    "Servant of Reality", "Sitting in the Buddha\u2019s Waiting Room",
    "We Are All Translators", "Small Boat, Great Mountain", "The Breakthrough",
    "Finding the Missing Peace", "Inner Listening", "Silent Rain", "The Island",
    "Broad View, Boundless Heart", "Tudong, The Long Road North",
    "Don\u2019t Push", "I\u2019m Right, You\u2019re Wrong!",
    "For the Love of the World", "Who Is Pulling The Strings",
    "Still Flowing Water", "Blank Page", "Buddhadasa Indapanno Archives",
}

ds_files = sorted([f for f in os.listdir(DD) if f.endswith(".jsonl") and not f.startswith("master_") and f not in ("train.jsonl","val.jsonl")])
ds_names_lower = set()
for f in ds_files:
    ds_names_lower.add(f.lower().replace("_"," ").replace(" qa.jsonl",""))

for b in sorted(os.listdir(ED)):
    bp = os.path.join(ED, b)
    if not os.path.isdir(bp): continue
    mp = os.path.join(bp, "metadata.json")
    if not os.path.exists(mp): continue
    with open(mp, "r", encoding="utf-8") as f:
        m = json.load(f)
    title = m.get("title", b)
    words = m.get("total_words", 0)
    if words < 10000: continue
    if title in CUSTOM_MAP_TITLES: continue

    # fuzzy check
    ct = title.lower().replace("'","").replace("\u2019","").replace(",","").replace("!","").replace("?","").replace(":","")
    found = False
    for dn in ds_names_lower:
        if dn in ct or ct in dn:
            found = True
            break
    if not found:
        nchs = len(m.get("chapters", []))
        sub_chs = len([c for c in m.get("chapters", []) if c.get("word_count",0) >= 200])
        print(f"MISSING: {title[:60]:60} | {words:>8,} w | {sub_chs:>3} substantive chs | dir: {b}")
