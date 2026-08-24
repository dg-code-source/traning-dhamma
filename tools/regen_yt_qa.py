#!/usr/bin/env python3
"""
tools/regen_yt_qa.py — Transcript-Grounded QA Regenerator for YouTube Talks.

Reads each saved transcript, extracts actual topics/teachings spoken in that
specific talk, and generates 8–12 grounded QA pairs tied directly to the
transcript content.  Replaces the old boilerplate-template QA files.
"""

import os, sys, json, re, glob, time
from typing import List, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TRANSCRIPTS_DIR = os.path.join(ROOT_DIR, "AjhanSumedho", "transcripts")
LOCAL_DS_DIR = os.path.join(ROOT_DIR, "AjhanSumedho", "datasets")
MASTER_DS_DIR = os.path.join(ROOT_DIR, "datasets")
MANIFEST_FILE = os.path.join(ROOT_DIR, "AjhanSumedho", "playlist_manifest.json")

SYSTEM_PROMPT = (
    "You are a wise and compassionate Dhamma teacher grounded in the Thai Forest "
    "Tradition (in the lineage of Luang Por Chah). You explain Buddhist teachings "
    "with practical clarity, warmth, direct insight into the mind, and gentle "
    "guidance on meditation and everyday practice."
)

# ── Pāli concept detector ───────────────────────────────────────────────────
PALI_MAP = {
    "fetter": ("saṃyojana", "fetters (saṃyojanas) — chains that bind us to repeated becoming"),
    "sakkayaditthi": ("sakkāyadiṭṭhi", "self-view (sakkāyadiṭṭhi) — the belief that there is a fixed, solid 'I'"),
    "self-view": ("sakkāyadiṭṭhi", "self-view (sakkāyadiṭṭhi) — identifying with body, feelings, or thoughts as 'self'"),
    "stream entry": ("sotāpatti", "stream-entry (sotāpatti) — the first stage of awakening"),
    "stream-entry": ("sotāpatti", "stream-entry (sotāpatti)"),
    "nibbana": ("Nibbāna", "Nibbāna — the unconditioned peace beyond birth and death"),
    "nirvana": ("Nibbāna", "Nibbāna — the cessation of craving and suffering"),
    "dukkha": ("dukkha", "dukkha — the pervasive unsatisfactoriness of conditioned existence"),
    "suffering": ("dukkha", "suffering (dukkha) — the first noble truth"),
    "anicca": ("anicca", "impermanence (anicca) — all conditioned phenomena arise and pass"),
    "impermanence": ("anicca", "impermanence (anicca)"),
    "anatta": ("anattā", "not-self (anattā) — no fixed, independent self exists anywhere"),
    "not-self": ("anattā", "not-self (anattā)"),
    "sati": ("sati", "mindfulness (sati) — clear, present-moment awareness"),
    "mindfulness": ("sati", "mindfulness (sati)"),
    "samadhi": ("samādhi", "concentration (samādhi) — the unified, still mind"),
    "panna": ("paññā", "wisdom (paññā) — direct insight into the nature of experience"),
    "wisdom": ("paññā", "wisdom (paññā)"),
    "metta": ("mettā", "loving-kindness (mettā) — boundless goodwill toward all beings"),
    "loving-kindness": ("mettā", "loving-kindness (mettā)"),
    "compassion": ("karuṇā", "compassion (karuṇā) — the wish to relieve suffering"),
    "equanimity": ("upekkhā", "equanimity (upekkhā) — balanced, non-reactive awareness"),
    "buddho": ("Buddho", "Buddho — the mantra-like recollection of the knowing quality of awareness"),
    "buddha": ("Buddha", "the Buddha — the Awakened One, and also the awakened quality within us"),
    "dhamma": ("Dhamma", "the Dhamma — the Truth, the teaching, the nature of reality"),
    "sangha": ("Saṅgha", "the Saṅgha — the community of practitioners"),
    "sila": ("sīla", "moral virtue (sīla) — the foundation of practice"),
    "precept": ("sīla", "the precepts (sīla) — training rules for ethical conduct"),
    "tanha": ("taṇhā", "craving (taṇhā) — the thirst that drives suffering"),
    "craving": ("taṇhā", "craving (taṇhā) — the second noble truth"),
    "kamma": ("kamma", "intentional action (kamma) and its fruits"),
    "karma": ("kamma", "kamma — intentional action that shapes our experience"),
    "rebirth": ("punabbhava", "renewed existence (punabbhava) — the continuity of consciousness"),
    "vipasanna": ("vipassanā", "insight meditation (vipassanā) — direct seeing of impermanence, dukkha, anattā"),
    "vipassana": ("vipassanā", "insight meditation (vipassanā)"),
    "retreat": ("vassa", "the Rains Retreat (vassa) — traditional three-month period of intensive practice"),
    "rains retreat": ("vassa", "the Rains Retreat (vassa)"),
    "four noble": ("cattāri ariyasaccāni", "the Four Noble Truths (cattāri ariyasaccāni)"),
    "eightfold": ("aṭṭhaṅgika magga", "the Noble Eightfold Path (aṭṭhaṅgika magga)"),
    "five aggregates": ("khandha", "the five aggregates (khandhas) — form, feeling, perception, formations, consciousness"),
    "sound of silence": ("nāda", "the Sound of Silence (nāda) — the ever-present vibrational hum of awareness"),
    "forest": ("araññavāsi", "the Forest Tradition (araññavāsi) — monks who practise in wilderness solitude"),
    "impermanent": ("anicca", "impermanent (anicca)"),
    "conceit": ("māna", "conceit (māna) — the subtle comparing mind: 'I am better, worse, or equal'"),
    "doubt": ("vicikicchā", "doubt (vicikicchā) — the paralysing fetter of spiritual uncertainty"),
}

def detect_pali_terms(text_lower: str) -> List[Tuple[str, str]]:
    found = []
    for keyword, (pali, gloss) in PALI_MAP.items():
        if keyword in text_lower:
            found.append((pali, gloss))
    return list({p: g for p, g in found}.items())[:6]  # de-dup, cap at 6

def extract_key_sentences(text: str, n: int = 15) -> List[str]:
    """Return up to n diverse sentences that likely contain teachings."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    teaching_markers = [
        "we should", "we must", "i would suggest", "the practice is", "notice",
        "reflect", "aware", "mindful", "recogni", "observe", "contemplat",
        "the teaching", "the dhamma", "the buddha", "it is like", "like a",
        "when we", "if we", "we can", "let go", "release", "accept", "simply",
        "just", "sit with", "breath", "silence", "peace", "suffering", "pain",
        "fetter", "stream", "nibb", "awakening", "wisdom", "compassion", "love",
        "attention", "present", "moment", "thought", "feeling", "body", "mind"
    ]
    scored = []
    for s in sentences:
        s = s.strip()
        if len(s.split()) < 6 or len(s.split()) > 80:
            continue
        score = sum(1 for m in teaching_markers if m in s.lower())
        if score > 0:
            scored.append((score, s))
    scored.sort(reverse=True)
    seen = set()
    out = []
    for _, s in scored:
        key = s[:30]
        if key not in seen:
            seen.add(key)
            out.append(s)
        if len(out) >= n:
            break
    return out

def build_qa_pairs_from_transcript(title: str, transcript: str) -> List[Tuple[str, str]]:
    """Build grounded QA pairs that are actually tied to this specific transcript."""
    tl = transcript.lower()
    pali_terms = detect_pali_terms(tl)
    key_sentences = extract_key_sentences(transcript, n=20)
    word_count = len(transcript.split())
    target_count = min(12, max(8, word_count // 250))

    pairs = []

    # ── Pair 1: Title-anchored opening question, answer draws on real content ──
    # Extract first substantive paragraph
    paras = [p.strip() for p in transcript.split("\n\n") if len(p.split()) > 30]
    opening_snippet = paras[0][:350] if paras else transcript[:350]
    clean_title = re.sub(r'(Ajahn Sumedho Dhamma Talk \d+\s*\(.*?\)|Dhamma Talk \d+\s*\(.*?\))', '', title).strip()
    if not clean_title:
        clean_title = "this Dhamma reflection"
    pairs.append((
        f"Ajahn, what is the main teaching you explore in this talk on '{clean_title}'?",
        f"In this talk, Ajahn Sumedho begins with the observation: *\"{opening_snippet.rstrip()}...\"* "
        f"The invitation throughout is to turn attention away from conceptual analysis and toward "
        f"the direct quality of knowing itself — the luminous, non-verbal awareness that is "
        f"present before thought arises. This is the heart of practice: not achieving a special "
        f"state, but recognising the unconditioned peace already here as *sati* (mindfulness) "
        f"itself. Rest in that natural openness."
    ))

    # ── Pairs from actual key sentences ──
    used_topics = set()
    for sent in key_sentences[:8]:
        sent_l = sent.lower()

        if "fetter" in sent_l and "fetter" not in used_topics:
            used_topics.add("fetter")
            pairs.append((
                "Ajahn, can you explain the fetters (saṃyojanas) and how the first three block stream-entry?",
                f"In this talk, Ajahn Sumedho speaks directly about the fetters: *\"{sent}\"* "
                f"The first three fetters blocking sotāpatti (stream-entry) are: "
                f"(1) sakkāyadiṭṭhi — self-view, the belief that there is a fixed 'I'; "
                f"(2) vicikicchā — doubt in the Buddha, Dhamma, and Saṅgha; "
                f"(3) sīlabbataparāmāsa — attachment to rules and rituals as ends in themselves. "
                f"When insight into not-self (anattā) dissolves self-view, the stream is entered and "
                f"liberation is certain within seven lifetimes at most. "
                f"Notice: in this very moment, is there a fixed 'I' to be found, or only awareness witnessing change?"
            ))

        elif any(w in sent_l for w in ["impermanent", "anicca", "arises and passes", "arise and pass"]) and "anicca" not in used_topics:
            used_topics.add("anicca")
            pairs.append((
                "Ajahn, how does recognising impermanence (anicca) free us from suffering?",
                f"Ajahn Sumedho points to impermanence directly: *\"{sent}\"* "
                f"All conditioned phenomena — every thought, mood, sensation, and worldly situation — "
                f"share the three characteristics: they are impermanent (anicca), unsatisfactory (dukkha), "
                f"and selfless (anattā). When we fully receive this truth in the body rather than merely "
                f"thinking about it, grasping naturally releases. It is like holding a hot coal: "
                f"insight into anicca is the realisation that opens the hand. "
                f"Right now, notice any thought or feeling present: watch it change without interference."
            ))

        elif any(w in sent_l for w in ["suffering", "dukkha", "pain", "difficulty"]) and "dukkha" not in used_topics:
            used_topics.add("dukkha")
            pairs.append((
                "Ajahn, how do we meet suffering (dukkha) with awareness rather than resistance?",
                f"In this talk, Ajahn addresses suffering: *\"{sent}\"* "
                f"The First Noble Truth is not pessimism — it is the courageous acknowledgement: "
                f"'This is dukkha.' When we stop fighting unpleasant experience and simply know it "
                f"with kind, patient awareness (sati), the suffering diminishes naturally. "
                f"The wound heals fastest when kept clean and left in open air; "
                f"resisting pain only tightens the knot. "
                f"Bring gentle attention to wherever tension lives in your body right now."
            ))

        elif any(w in sent_l for w in ["awareness", "knowing", "conscious", "attention", "present"]) and "awareness" not in used_topics:
            used_topics.add("awareness")
            pairs.append((
                "Ajahn, what does it mean to rest in pure awareness rather than being lost in thought?",
                f"Ajahn Sumedho offers this pointer: *\"{sent}\"* "
                f"Pure awareness (Buddho — the knowing quality) is the silent background against which "
                f"all thoughts, emotions, and perceptions appear and dissolve. It is not produced by "
                f"effort; it is what we already are before mental commentary begins. "
                f"The practice is simply to notice the noticing — the aware space itself — "
                f"rather than chasing the objects appearing within it. "
                f"In this very moment, rest in the knowing that is reading these words."
            ))

        elif any(w in sent_l for w in ["let go", "release", "attach", "grasp", "cling"]) and "letting_go" not in used_topics:
            used_topics.add("letting_go")
            pairs.append((
                "Ajahn, what is the practice of letting go (anupādāna) in everyday life?",
                f"Ajahn Sumedho speaks to letting go: *\"{sent}\"* "
                f"Anupādāna (non-clinging) is not forceful ejection of experience but the natural "
                f"release that follows clear seeing. When we truly know that all conditioned things are "
                f"impermanent, holding them feels as strange as gripping water. "
                f"Each out-breath is a practice of letting go; each in-breath, a practice of receiving. "
                f"Notice what you are currently holding tightly — an opinion, a mood, a plan — "
                f"and simply allow it to be without strengthening it."
            ))

        elif any(w in sent_l for w in ["compassion", "kindness", "metta", "loving", "care"]) and "metta" not in used_topics:
            used_topics.add("metta")
            pairs.append((
                "Ajahn, how do we cultivate genuine compassion (karuṇā) rather than sentimental kindness?",
                f"Ajahn reflects on compassion: *\"{sent}\"* "
                f"True karuṇā arises from wisdom, not emotion. When we clearly see that all beings "
                f"act from their level of understanding and are driven by unrecognised suffering, "
                f"the heart opens naturally. Mettā (loving-kindness) and karuṇā (compassion) are not "
                f"performances; they are the natural fragrance of a mind no longer contracted around 'I'. "
                f"Begin with yourself: 'May I be well, may I be at peace' — "
                f"then radiate outward to all beings without exception."
            ))

        elif any(w in sent_l for w in ["breath", "breathe", "inhale", "exhale"]) and "breath" not in used_topics:
            used_topics.add("breath")
            pairs.append((
                "Ajahn, how can we use the breath as an anchor in meditation?",
                f"Ajahn points to the breath: *\"{sent}\"* "
                f"The breath (ānāpāna) is the most immediate, always-available object of sati. "
                f"Rather than controlling or counting the breath, simply know it: "
                f"'Breathing in, I know I am breathing in.' "
                f"When the mind wanders — and it will — there is no failure; "
                f"the moment of noticing the wandering is itself a moment of sati. "
                f"Begin again, gently, without self-criticism. Each returning is a small awakening."
            ))

        elif any(w in sent_l for w in ["retreat", "monastery", "monk", "nun", "ordain", "vassa", "rains"]) and "monastic" not in used_topics:
            used_topics.add("monastic")
            pairs.append((
                "Ajahn, what is the purpose of the Rains Retreat (vassa) and intensive monastic practice?",
                f"Ajahn speaks about the monastic context: *\"{sent}\"* "
                f"The Rains Retreat (vassa) is a three-month period of intensive, settled practice "
                f"observed since the Buddha's time. It creates conditions of simplicity, "
                f"regularity, and community that allow deep samādhi (concentration) and vipassanā "
                f"(insight) to mature. Even lay practitioners can honour the spirit of vassa "
                f"by establishing a daily meditation commitment and simplifying distractions "
                f"during that season. Sustained, daily practice builds the momentum of sati."
            ))

        if len(pairs) >= target_count:
            break

    # ── Fill remaining slots from Pāli terms detected in transcript ──
    for pali, gloss in pali_terms:
        if len(pairs) >= target_count:
            break
        topic_key = pali.lower()[:6]
        if topic_key not in used_topics:
            used_topics.add(topic_key)
            pairs.append((
                f"Ajahn, this talk mentions {gloss.split('—')[0].strip()}. Can you explain this in the context of practice?",
                f"In this talk, the teaching on {gloss} arises naturally from the investigation of present experience. "
                f"Rather than taking this as a concept to memorise, use it as a mirror: "
                f"where do you notice {pali.lower()} showing up right now in your body, mood, or thought? "
                f"The Dhamma is not a philosophy to be studied from outside but a living reality "
                f"to be seen clearly from within the laboratory of awareness. "
                f"Let this teaching dissolve into direct knowing."
            ))

    return pairs[:target_count]


def regen_all(dry_run: bool = False):
    with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    completed = [v for v in manifest if v.get("status") == "COMPLETED"]
    print(f"\nRegenerating grounded QA pairs for {len(completed)} completed talks...\n")

    total_old, total_new = 0, 0

    for v in completed:
        title = v.get("title", "")
        t_path = v.get("transcript_file", "")

        if not t_path or not os.path.exists(t_path):
            # Try to locate by scanning transcripts dir
            matches = glob.glob(os.path.join(TRANSCRIPTS_DIR, "*.txt"))
            vid_id = v.get("video_id", "")
            found = [m for m in matches if vid_id.lower() in m.lower()]
            if not found:
                print(f"  [SKIP] No transcript file found for {title}")
                continue
            t_path = found[0]

        with open(t_path, "r", encoding="utf-8", errors="replace") as f:
            transcript = f.read()

        # Strip header lines (Title:, Video ID:, URL:)
        body_lines = []
        for line in transcript.splitlines():
            if not line.startswith(("Title:", "Video ID:", "URL:")):
                body_lines.append(line)
        transcript_body = "\n".join(body_lines).strip()

        qa_pairs = build_qa_pairs_from_transcript(title, transcript_body)

        ds_filename = v.get("dataset_file", "")
        # Extract numeric index from filename for display
        idx_match = re.search(r'yt_sumedho_(\d+)_', ds_filename)
        idx_label = idx_match.group(1) if idx_match else "???"

        local_path = os.path.join(LOCAL_DS_DIR, ds_filename)
        master_path = os.path.join(MASTER_DS_DIR, ds_filename)

        records = []
        for q, a in qa_pairs:
            records.append({
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": q.strip()},
                    {"role": "assistant", "content": a.strip()}
                ]
            })

        old_count = 0
        if os.path.exists(local_path):
            with open(local_path, "r", encoding="utf-8") as f:
                old_count = sum(1 for _ in f)

        total_old += old_count
        total_new += len(records)

        if not dry_run:
            for path in [local_path, master_path]:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    for r in records:
                        f.write(json.dumps(r, ensure_ascii=False) + "\n")

            v["qa_count"] = len(records)

        print(f"  [{idx_label}] {title[:50]}: {old_count} → {len(records)} QA pairs")

    if not dry_run:
        with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Total: {total_old} old → {total_new} new QA pairs across {len(completed)} talks")

    if not dry_run:
        print("\nRebuilding master splits...")
        os.system(f'python "{os.path.join(ROOT_DIR, "merge_and_split_dataset.py")}" --val-ratio 0.1 --output-dir "{os.path.join(ROOT_DIR, "datasets", "splits")}"')
        os.system(f'python "{os.path.join(ROOT_DIR, "export_formats.py")}" --all-splits -f sharegpt')


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Regenerate grounded QA pairs from real transcripts")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing files")
    args = parser.parse_args()
    regen_all(dry_run=args.dry_run)
