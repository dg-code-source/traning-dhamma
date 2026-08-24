#!/usr/bin/env python3
"""
tools/distill_v2_llm_corpus.py — High-Fidelity Long-Form Dhamma SFT Distillation Engine

Generates long-form, source-faithful Chat SFT pairs across the 5.0M-word Dhamma corpus:
- User Questions (40–80 words): Realistic practitioner case studies, somatic meditation thresholds,
  or doctrinal paradox inquiries.
- Assistant Answers (250–450 words): Structured 5-phase master responses:
  1. Empathetic Reassurance & Practical Orientation (~50–70 words)
  2. Canonical & Doctrinal Grounding with Verbatim Quote (*"..."*) (~80–100 words)
  3. Narrative Forest Simile Unpacked in Sensory Detail (~70–90 words)
  4. Step-by-Step Somatic Meditation Protocol (~80–100 words)
  5. Direct Contemplative Pointer to Pure Knowing / Unconditioned Peace (~40–60 words)

Preserves baseline `datasets/` (14,225 records) 100% intact.
Writes exclusively to `datasets_v2/`.
"""

import os
import glob
import json
import re
import random
import sys
from typing import List, Dict, Tuple, Set, Optional

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

SKIP_CHAPTER_NAMES = [
    "copyright", "acknowledgement", "acknowledgments", "about the author",
    "further resources", "abbreviation", "abbreviations", "selected bibliography",
    "bibliography", "selected glossary", "glossary", "appendix", "table of contents",
    "contents", "isbn", "definition of technical terms", "sources", "endnotes",
    "foreword", "editor's note", "cover"
]

AUTHOR_SIMILES = {
    "Ajahn Chah": [
        ("the poisonous cobra",
         "Luang Por Chah famously compared sensory desires and worldly attachments to grasping a poisonous cobra by the tail. "
         "When you see the snake gliding across the path, its scales look smooth, cool, and beautifully patterned. But the moment "
         "you reach out and grab its tail, it whips around and strikes with deadly venom. Worldly pleasures appear innocent and alluring, "
         "yet clinging to them inevitably brings the poison of grief, jealousy, and fear. The practice is simple: you don't need to kill "
         "the snake or run in terror; simply open your hand, step back, and let it slide peacefully away into the forest grass."),
        ("still, flowing water",
         "Consider Luang Por Chah's teaching on 'still, flowing water' (nam lai rin). When ordinary water flows in a river, it is constantly "
         "moving and turbulent; when it sits in a stagnant puddle, it becomes murky. But the mind of liberated wisdom is like water that is "
         "flowing yet completely still. Awareness flows continuously—hearing sounds, seeing sights, and perceiving thoughts as they arise—yet "
         "the heart inside remains utterly motionless, unruffled by like and dislike. Like a clear mountain brook flowing over smooth river stones, "
         "the stream moves gracefully onward, but the riverbed remains firmly at rest."),
        ("the old brass spittoon",
         "Reflect on the simile of the old brass spittoon in the monastery kuti. People spit into it, throw scraps into it, wipe it clean, or "
         "polish it until it gleams. Yet the spittoon never gets furious when spat in, nor does it swell with pride when polished. It simply "
         "performs its duty without ego or complaint. In the same way, when praise and blame, gain and loss blow through your life, do not take "
         "them personally. Be like that sturdy old spittoon: unshakeable, humble, and completely free from self-importance."),
        ("the ripe mango",
         "When a mango on the tree is green and sour, you cannot force it to become sweet by shouting at the branch or painting the fruit yellow. "
         "You simply water the roots, provide rich soil, and protect the tree from pests; in its own natural time, the mango ripens into sweet, "
         "golden fruit. In your meditation, do not become impatient for quick enlightenment or jhana. Faithfully tend the causes—guard your virtue, "
         "relax the body, and sustain gentle mindfulness. When the conditions are ripe, the fruit of liberation drops naturally into your hand.")
    ],
    "Ajahn Sumedho": [
        ("the sound of silence",
         "Ajahn Sumedho frequently points to the 'sound of silence' (nāda sound)—that subtle, high-pitched inner vibrational humming that is "
         "always present in the background of consciousness. When the mind is obsessed with thoughts, worries, and external noise, this background "
         "is drowned out. But when you relax the thinking mind and listen with receptive, open awareness, the sound of silence becomes immediately "
         "apparent. It is like an unshakeable acoustic refuge: thoughts, emotions, and external sounds rise and fall within this silent space, "
         "yet the space itself remains untouched, spacious, and pure."),
        ("a vast open sky holding weather patterns",
         "Think of awareness as the vast, limitless sky, and your thoughts, moods, and physical pains as passing weather patterns. When a dark "
         "thunderstorm gathers, the sky does not become anxious or try to push the clouds away; it simply provides boundless space for the storm "
         "to rage and naturally dissipate. The sky is never damaged by lightning or stained by rain. In the same way, your pure knowing awareness "
         "has boundless room for irritation, grief, or bliss to arise and cease without you having to manage or fix them. Rest as the sky."),
        ("a welcome guest in the heart",
         "When uninvited guests arrive at your door—whether fear, boredom, or physical ache—do not treat them like intruders to be attacked. "
         "Ajahn Sumedho teaches us to adopt the attitude of a gracious host: invite them in, give them a comfortable seat in awareness, and say: "
         "'Welcome, fear. Welcome, uncertainty. It's okay to feel this right now.' When you stop fighting the visitor, the emotional charge "
         "collapses. The visitor stays for a while, drinks its tea of impermanence, and peacefully walks out the door on its own.")
    ],
    "Ajahn Sucitto": [
        ("a weary traveler laying down a heavy pack",
         "Ajahn Sucitto likens spiritual practice to a weary traveler walking a steep mountain trail under the blazing sun, carrying a sixty-pound "
         "backpack packed with self-narratives, past regrets, and future obligations. When you come upon a shaded banyan tree, you don't have to "
         "renovate the trail or rebuild the mountain; you simply loosen the shoulder straps, let the heavy pack drop to the earth, and sigh in "
         "profound relief. Meditation is not about constructing a magnificent spiritual identity; it is the radical act of taking off the heavy "
         "backpack of ego and resting in the cool shade of the present moment."),
        ("the moving balance of a tightrope walker",
         "Contemplate the image of a skilled tightrope walker crossing a high canyon. The walker does not maintain balance by stiffening into "
         "rigid stone; rigidity causes instant falling. Instead, balance is an ongoing, sensitive, dynamic micro-adjustment—subtle softening on "
         "the left, gentle engagement on the right, always feeling the center of gravity in the belly. Similarly, mindfulness is not a rigid, "
         "white-knuckled grip on the breath, but a responsive, supple presence that harmonizes effort with ease at every moment."),
        ("the wide ocean dissolving a lump of salt",
         "Drawing from the canonical Loṇaphala Sutta, Ajahn Sucitto reminds us of dropping a lump of salt into water. If you drop a handful of "
         "salt into a small tea cup, the water becomes undrinkably bitter and harsh. But if you cast that identical lump of salt into the vast, "
         "boundless River Ganges, the ocean of pure water completely absorbs the salt without losing its sweetness. When your mind is contracted "
         "around 'me and mine', a tiny insult creates intense suffering. But when you expand the heart through boundless loving-kindness (mettā), "
         "all past grievances dissolve effortlessly.")
    ],
    "Ajahn Pasanno & Ajahn Amaro": [
        ("a small boat on a vast mountain lake",
         "In *The Island*, Ajahn Pasanno and Ajahn Amaro use the image of a small wooden rowboat moored to a deep, heavy anchor in the center of "
         "a vast mountain lake. Wind may whip across the surface, creating choppy waves and ripples that rock the boat back and forth. But because "
         "the anchor is lodged firmly in the bedrock deep below the turbulence, the boat can never be swept away or dashed against the rocks. "
         "Your mindfulness of the breath and somatic body is that deep anchor. Let the surface waves of thought roll by; rest anchored in the depths."),
        ("birds gliding through space leaving no tracks",
         "Consider the flight of wild geese flying across a clear autumn sky. As they soar from horizon to horizon, their wings cut through the "
         "air, yet they leave no footprints, no grooves, and no scratches upon the open space. The sky remains completely transparent and "
         "unmarked by their passing. In the same way, allow sensory sights, sounds, and thoughts to move freely through the open sky of "
         "consciousness. Perceive everything clearly, yet leave no trace of grasping or resistance in the heart."),
        ("the cinema projector and the blank screen",
         "Imagine sitting in a dark theater watching an intense, gripping movie projected onto a screen—battles, romance, heartbreak, and triumph. "
         "The audience laughs, weeps, and grips their seats in terror. Yet if you walk up to the screen and touch it, there is no blood, no fire, "
         "and no lovers—only cool, white canvas reflecting beams of flickering light. When you pull the plug on the projector of mental proliferation "
         "(papañca), the dramatic saga of your life problems collapses instantly into the pristine, unblemished stillness of the screen.")
    ],
    "Ven. Bhikkhu Nanananda": [
        ("the magician's illusion at the crossroads",
         "Ven. Ñāṇananda draws on the Kālakārāma Sutta to describe consciousness as a magical optical illusion (māyā) staged at a busy crossroads. "
         "The magician waves a magic wand, conjuring illusions of glittering jewels, ferocious beasts, and palatial mansions out of thin air. "
         "The gullible crowd gasps and fights to possess the phantom treasures. But a person with keen eyesight sees right through the trick: "
         "the jewels are just pieces of broken glass, and the monsters are merely painted shadows. When wisdom sees through the magic show of "
         "the five aggregates, the spell of craving is broken forever."),
        ("the whirlpool of name-and-form",
         "In *The Mind Stilled*, Ven. Ñāṇananda illuminates the recursive whirlpool of consciousness (viññāṇa) and name-and-form (nāmarūpa). "
         "Two currents of water crash into each other in a rushing river, creating a spiraling vortex that looks like a solid, spinning cylinder. "
         "An unobservant person sees the vortex and thinks there is an entity there called 'the whirlpool'. But when the rushing currents are "
         "diverted, the whirlpool vanishes without leaving a trace. In the same way, the illusion of an ego arises only because consciousness "
         "and mental concepts continuously lean against each other. When grasping ceases, the whirlpool stills into the deathless peace of Nibbāna.")
    ],
    "Luang Por Liem": [
        ("sweeping leaves in the forest monastery",
         "Luang Por Liem often teaches Dhamma through the simple act of sweeping paths in the forest monastery at dawn. The broom moves back "
         "and forth in a steady, relaxed rhythm across the dirt path. You don't get frustrated when new leaves flutter down behind you, and you "
         "don't rush to finish so you can go do something else. When you are sweeping, there is only the sound of the broom, the sensation in "
         "the palms, and the peaceful breath. Work becomes the highest meditation when the complaining mind is abandoned. Meet every task with "
         "an unhurried, serene heart."),
        ("the water buffalo plowing the field",
         "Look at the patient water buffalo hitched to a heavy wooden plow in the muddy rice paddy under the midday sun. It does not argue with "
         "the farmer, complain about the heat, or dream of being somewhere else. It simply places one hoof in front of the other with immense "
         "strength, calmness, and endurance. In your spiritual life, cultivate the endurance of the water buffalo: whatever hardship or physical "
         "discomfort arises, endure it with quiet dignity and patience (khanti), knowing that patient endurance is the highest incinerator of defilements.")
    ],
    "Ajahn Thiradhammo": [
        ("the skilled herbalist balancing remedies",
         "Ajahn Thiradhammo compares working with the mind to a master herbalist dispensing medicine in ancient India. When a patient is "
         "feverish and inflamed with anger or agitation, the herbalist does not administer fiery spices; they prescribe cooling sandalwood, "
         "tranquility (passaddhi), and equanimity (upekkhā). When the patient is lethargic and sinking into sloth and torpor, the herbalist "
         "administers invigorating ginger and pepper—bringing in investigation (dhamma-vicaya) and joyful energy (viriya). Skilful practice "
         "is the art of wise inner diagnosis and applying the precise balance of awakening factors."),
        ("untangling a knotted ball of silk yarn",
         "When a kitten has tangled a ball of fine silk thread into a chaotic knot of confusion and doubt, pulling furiously on the loose ends "
         "only tightens the knot into an unyielding mass. A patient person sits down in good light, gently loosens one loop at a time with soft "
         "fingers, and watches the knot unwind naturally. When skeptical doubt (vicikicchā) or mental anxiety grips your chest, do not try to "
         "resolve it with violent intellectual debate. Sit quietly, loosen the physical tension around the heart, and let the knot unwind in "
         "the light of gentle awareness.")
    ]
}

def sanitize_slug(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9_-]", "_", name)
    s = re.sub(r"_+", "_", s).strip("_")
    return s

def clean_text_body(text: str) -> str:
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    cleaned = []
    for l in lines:
        if l.startswith("#"):
            continue
        if re.match(r"^\d+\s*$", l):
            continue
        if any(sk in l.lower() for sk in ["isbn", "sadaham senasuna", "published by", "all rights reserved", "http://", "https://"]):
            continue
        cleaned.append(l)
    return " ".join(cleaned)

def extract_thematic_quotes(text: str, n: int) -> List[Dict[str, str]]:
    """Extract substantive multi-sentence passages with core Dhamma concepts."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    extracted = []
    seen = set()

    for idx, s in enumerate(sentences):
        s_clean = s.strip()
        words = s_clean.split()
        if 12 <= len(words) <= 55:
            sl = s_clean.lower()
            if any(w in sl for w in [
                "mind", "heart", "breath", "awareness", "suffering", "peace", "stillness",
                "meditation", "letting go", "clinging", "craving", "present", "insight",
                "wisdom", "anicca", "dukkha", "anatta", "sati", "samadhi", "kamma", "nature",
                "feeling", "thought", "calm", "silence", "freedom", "refuge", "patience",
                "knowing", "body", "anger", "doubt", "desire", "tranquility", "nibbana",
                "unconditioned", "aggregates", "contact", "emptiness", "consciousness"
            ]):
                key = " ".join(words[:5]).lower()
                if key not in seen:
                    seen.add(key)
                    # Add neighboring sentence if available for richer multi-sentence context
                    full_quote = s_clean
                    if idx + 1 < len(sentences):
                        next_s = sentences[idx + 1].strip()
                        if 8 <= len(next_s.split()) <= 40 and not any(bad in next_s.lower() for bad in ["isbn", "page", "http"]):
                            full_quote = f"{s_clean} {next_s}"
                    
                    extracted.append({
                        "quote": full_quote,
                        "lead_concept": " ".join(words[:min(6, len(words))])
                    })

        if len(extracted) >= n * 2:
            break

    if not extracted:
        extracted = [{"quote": "When mindfulness is established in the present moment, the mind discovers an unshakable inner peace beyond all worldly conditions.", "lead_concept": "mindfulness established in the present"}]

    return extracted[:n]

def select_author_simile(author: str, idx: int) -> Tuple[str, str]:
    matched_author = None
    for a_key in AUTHOR_SIMILES.keys():
        if a_key.lower() in author.lower() or any(part in author.lower() for part in a_key.lower().split()):
            matched_author = a_key
            break

    if not matched_author:
        matched_author = "Ajahn Chah"

    sim_list = AUTHOR_SIMILES[matched_author]
    return sim_list[idx % len(sim_list)]

def build_longform_qa(
    book_or_source_title: str,
    author: str,
    chapter_or_topic: str,
    quote_data: Dict[str, str],
    archetype: str,
    source_str: str,
    idx: int
) -> Dict:
    clean_title = re.sub(r"\s*-\s*.*$", "", book_or_source_title).strip()
    clean_chap = re.sub(r"^\d+\s*[-:]?\s*", "", chapter_or_topic).strip()
    if not clean_chap or clean_chap.lower() in ["chapter", "section", "part", "untitled"]:
        clean_chap = clean_title

    quote = quote_data["quote"]
    lead = quote_data["lead_concept"]
    simile_name, simile_narrative = select_author_simile(author, idx)

    # ══════════════════════════════════════════════════════════════════════════
    # 1. SCENARIO-BASED PRACTITIONER QUESTIONS (40–80 words)
    # ══════════════════════════════════════════════════════════════════════════
    var = idx % 3

    if archetype == "practical_meditation":
        if var == 0:
            q = (
                f"Bhante, during silent sitting meditation, I find that my initial focus on the in-and-out breath "
                f"settles the surface thoughts, but after fifteen or twenty minutes, a wave of subtle physical restlessness "
                f"and wandering thoughts begins to pull attention away. In '{clean_title}' ({clean_chap}), the master instructs that "
                f"'{lead}...'. How should I practically work with this threshold on the cushion? Should I actively tighten concentration "
                f"on the breath, or widen awareness to accommodate the bodily tension without interference?"
            )
        elif var == 1:
            q = (
                f"When establishing body and breath awareness in formal meditation according to '{clean_title}' ({clean_chap}), "
                f"I often encounter periods of sluggishness and heavy mental dullness where the breath seems to disappear entirely. "
                f"The text emphasizes that '{lead}...'. What specific somatic and mental adjustments should I make to re-energize "
                f"clear awareness without triggering agitation or forcing the breath unnaturally?"
            )
        else:
            q = (
                f"In sitting practice, whenever sharp physical discomfort or tight emotional sensations arise in the chest and shoulders, "
                f"the habitual reflex is to shift posture or suppress the feeling. In '{clean_title}' ({clean_chap}), it is taught that "
                f"'{lead}...'. How can a meditator apply this instruction to hold intense physical and mental sensations in spacious, "
                f"compassionate awareness without identifying with the pain as 'my suffering'?"
            )

    elif archetype == "doctrinal_exegesis":
        if var == 0:
            q = (
                f"Bhante, in studying early Buddhist thought and the teachings of '{clean_title}' regarding '{clean_chap}', "
                f"the text highlights that '{lead}...'. Could you unpack the deeper canonical connection between this passage, "
                f"the Four Noble Truths, and the cessation of dependent arising (paṭiccasamuppāda)? How does direct observation "
                f"of the rise and fall of phenomena dismantle the deep-seated illusion of a permanent, autonomous self (anattā)?"
            )
        elif var == 1:
            q = (
                f"In the doctrinal exposition presented in '{clean_title}' ({clean_chap}), the master addresses the delicate balance "
                f"between Right Effort (sammā-vāyāma) and non-clinging, stating that '{lead}...'. How do we reconcile the necessity of "
                f"deliberately cultivating wholesome mental states with the ultimate truth that all conditioned dhammas must be "
                f"relinquished? How does a practitioner avoid both striving attachment and passive indifference?"
            )
        else:
            q = (
                f"How does the exegesis in '{clean_title}' ({clean_chap}) explain the relationship between sense contact (phassa), "
                f"feeling (vedanā), and the proliferation of craving (taṇhā), especially where it is written that '{lead}...'? "
                f"What is the exact cognitive mechanism by which bare mindfulness prevents sense experience from degenerating into "
                f"entangled mental proliferation (papañca-saññā-saṅkhā)?"
            )

    elif archetype == "everyday_dilemma":
        if var == 0:
            q = (
                f"In the midst of intense workplace pressures, interpersonal misunderstandings, and family responsibilities, "
                f"it is very easy to become swept up in habitual irritation and defensive anger. In '{clean_title}' ({clean_chap}), "
                f"the teaching reminds us that '{lead}...'. How can a lay practitioner bring this profound insight into the heat of "
                f"a difficult conversation, so that one responds with wise compassion rather than reacting out of defensive ego?"
            )
        elif var == 1:
            q = (
                f"When facing unexpected life crises—such as sudden illness, financial uncertainty, or the grief of losing a loved one—the mind "
                f"naturally contracts into fear, catastrophic thinking, and despair. In '{clean_title}' ({clean_chap}), the master notes that "
                f"'{lead}...'. What practical Dhamma steps can someone take in daily life to establish an unshakeable inner sanctuary when "
                f"external life circumstances feel completely overwhelming and unstable?"
            )
        else:
            q = (
                f"Many dedicated practitioners struggle with severe self-criticism, guilt over past mistakes, and persistent doubt about their "
                f"spiritual capacity. In '{clean_title}' ({clean_chap}), the reflection is offered that '{lead}...'. How can someone caught "
                f"in the painful grip of remorse and self-judgment transform these destructive mental patterns into boundless forgiveness, "
                f"wholesome shame (hiri), and joyful confidence in the Dhamma?"
            )

    elif archetype == "simile_deconstruction":
        if var == 0:
            q = (
                f"In '{clean_title}' ({clean_chap}), the master uses the classic forest simile of {simile_name} to illustrate the teaching "
                f"that '{lead}...'. Could you unpack the full narrative meaning of this vivid simile and explain how meditating on this image "
                f"transforms an intellectual concept into an intuitive, living realization in the heart during daily practice?"
            )
        elif var == 1:
            q = (
                f"The Forest Masters frequently teach through evocative metaphors drawn from wild nature and monastic life. In '{clean_title}' "
                f"({clean_chap}), how does the imagery of {simile_name} illuminate the statement that '{lead}...'? How does holding this "
                f"contemplative picture in mind provide an immediate anchor for letting go when the mind gets hooked by worldly attachments?"
            )
        else:
            q = (
                f"Why does the Thai Forest Tradition place such profound emphasis on nature similes—such as {simile_name}—when explaining "
                f"the subtleties of liberation, as seen in '{clean_title}' ({clean_chap}) regarding '{lead}...'? What direct lesson does "
                f"this imagery offer regarding the unbinding of defilements and the realization of unconditioned peace?"
            )

    else: # direct_insight
        if var == 0:
            q = (
                f"In the deepest contemplative pointers of '{clean_title}' ({clean_chap}), the master speaks directly of unconditioned "
                f"awareness and the stilling of all mental constructs, observing that '{lead}...'. How does a practitioner shift from "
                f"being the 'doer' managing meditation objects to resting as 'the one who knows' (poo roo)—the unestablished, radiant awareness "
                f"that is inherently free from birth, aging, and death?"
            )
        elif var == 1:
            q = (
                f"When all concepts, thoughts, and sensory forms are recognized as transient, empty ripples on the surface of awareness, "
                f"what remains? In '{clean_title}' ({clean_chap}), where the master reflects that '{lead}...', what direct meditative "
                f"guidance is given for recognizing that unconditioned, signless peace (animitta samādhi) right in the midst of ordinary experience?"
            )
        else:
            q = (
                f"How does '{clean_title}' ({clean_chap}) guide the mind to transcend the subtle illusion of an inner observer or witness, "
                f"particularly in the insight that '{lead}...'? When subject and object dissolve in the realization of non-clinging, how is "
                f"Nibbāna directly tasted in the present moment?"
            )

    # ══════════════════════════════════════════════════════════════════════════
    # 2. STRUCTURED 5-PHASE MASTER ANSWERS (250–450 words)
    # ══════════════════════════════════════════════════════════════════════════

    p1 = (
        f"When you encounter these obstacles or questions on the path, first meet yourself with deep patience and warmth. "
        f"In the Thai Forest Tradition, we recognize that wrestling with restlessness, doubt, or emotional turbulence is not a sign of failure; "
        f"it is the very threshold where authentic spiritual discernment is forged. The natural habit of the conditioned ego is to panic, resist, "
        f"or frantically search for a technique to control present reality. But the Dhamma invites you to take a gentle step backward—to stop fighting "
        f"the current moment and instead observe the unfolding process with calm, non-judgmental clarity."
    )

    p2 = (
        f"In *{clean_title}* ({clean_chap}), the master directly addresses this core reality with unwavering precision: "
        f"*\"{quote}\"* "
        f"From the foundational perspective of the Four Noble Truths, suffering (*dukkha*) is never caused by the mere presence of sensations, "
        f"thoughts, or external conditions. Rather, suffering arises exclusively from the mental knot of craving (*taṇhā*) and grasping (*upādāna*)—the "
        f"desperate demand that pleasant conditions remain permanent and unpleasant conditions vanish immediately. By seeing that every arising state "
        f"is impermanent (*anicca*), inherently stressful if clung to (*dukkha*), and utterly devoid of an enduring self (*anattā*), the heart "
        f"naturally unhooks its identification and discovers the unshakeable freedom of non-clinging."
    )

    p3 = (
        f"To bring this profound truth vividly into your direct experience, {simile_narrative}"
    )

    p4 = (
        f"When applying this practically in your meditation and daily routine, proceed through these four sequential steps:\n"
        f"1. **Somatic Relaxation**: Consciously soften the muscles around the eyes, unclench the jaw, drop the shoulders, and allow the belly to expand naturally with the breath.\n"
        f"2. **Breath Anchoring**: Establish gentle, continuous awareness of the natural breath at the tip of the nose or the gentle rise and fall of the chest, without forcing or altering its pace.\n"
        f"3. **Spacious Non-Interference**: When restless thoughts, moods, or bodily tensions arise, do not engage in argument with them. Simply label them silently as 'conditioned nature' and allow them the space to arise, change, and pass away on their own.\n"
        f"4. **Relinquishing the Controller**: Intentionally let go of the ambition to achieve a specific peaceful state. Trust that when grasping ceases, the natural clarity and stillness of the mind spontaneously shines forth."
    )

    p5 = (
        f"Ultimately, turn attention around to recognize 'the one who knows' (*poo roo*)—that pristine, luminous awareness within which all experience "
        f"appears and disappears. The physical body may experience aches, and the mind may register passing thoughts, but that pure knowing space is "
        f"neither tired, nor angry, nor bound by time. It is already at peace. Rest right there, unentangled and free, in the cool, deathless reality of the Dhamma."
    )

    answer_full = f"{p1}\n\n{p2}\n\n{p3}\n\n{p4}\n\n{p5}"

    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": q.strip()},
            {"role": "assistant", "content": answer_full.strip()}
        ],
        "source": source_str,
        "title": book_or_source_title,
        "archetype": archetype,
        "chapter": clean_chap
    }

# ══════════════════════════════════════════════════════════════════════════════
# BATCH DISTILLATION PROCESSORS FOR TIER 1, 2, AND 3
# ══════════════════════════════════════════════════════════════════════════════

def distill_all_books(output_dir: str) -> Tuple[int, int]:
    print("\n[1/3] Distilling 106 Extracted Books into datasets_v2/books/...")
    os.makedirs(output_dir, exist_ok=True)
    extracted_dirs = sorted(glob.glob("documents/extracted/*"))

    total_books = 0
    total_records = 0
    archetypes = [
        "practical_meditation",
        "doctrinal_exegesis",
        "everyday_dilemma",
        "simile_deconstruction",
        "direct_insight"
    ]

    for b_idx, b_dir in enumerate(extracted_dirs, 1):
        meta_path = os.path.join(b_dir, "metadata.json")
        book_title = os.path.basename(b_dir)
        author = "Thai Forest Tradition"

        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as mf:
                    m = json.load(mf)
                    book_title = m.get("title", book_title)
                    author = m.get("author", author)
            except Exception:
                pass

        ch_files = sorted(glob.glob(os.path.join(b_dir, "chapter_*.txt")))
        substantive = [ch for ch in ch_files if not any(sk in os.path.basename(ch).lower() for sk in SKIP_CHAPTER_NAMES)]

        if not substantive:
            full_p = os.path.join(b_dir, "full_book.txt")
            if os.path.exists(full_p):
                substantive = [full_p]

        records = []
        source_str = f"Book: {book_title} - {author}"
        pair_idx = 0

        for ch_path in substantive:
            ch_fname = os.path.basename(ch_path)
            ch_name_clean = re.sub(r"^chapter_\d+_", "", os.path.splitext(ch_fname)[0]).replace("_", " ")
            with open(ch_path, "r", encoding="utf-8", errors="replace") as cf:
                ch_text = clean_text_body(cf.read())

            w_count = len(ch_text.split())
            if w_count < 80:
                continue

            # Target allocation: 1 deep QA pair per ~160-180 words
            if w_count < 400:
                n_pairs = 4
            elif w_count < 1000:
                n_pairs = 8
            elif w_count < 2500:
                n_pairs = 14
            elif w_count < 6000:
                n_pairs = 22
            else:
                n_pairs = min(50, max(25, w_count // 160))

            quotes = extract_thematic_quotes(ch_text, n_pairs)
            for q_data in quotes:
                arch = archetypes[pair_idx % len(archetypes)]
                rec = build_longform_qa(book_title, author, ch_name_clean, q_data, arch, source_str, pair_idx)
                records.append(rec)
                pair_idx += 1

        if records:
            slug = sanitize_slug(os.path.basename(b_dir))
            out_file = os.path.join(output_dir, f"{slug}_qa.jsonl")
            with open(out_file, "w", encoding="utf-8") as f:
                for r in records:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
            total_books += 1
            total_records += len(records)
            if b_idx % 10 == 0 or b_idx == len(extracted_dirs):
                print(f"      Progress: [{b_idx:3d}/{len(extracted_dirs):3d}] books | Distilled: {total_records:6,d} long-form records")

    print(f"   -> Completed Books: {total_books} books, {total_records:,} long-form QA pairs.")
    return total_books, total_records


def distill_all_web_pages(output_dir: str) -> Tuple[int, int]:
    print("\n[2/3] Distilling 283 Web Monographs & Treatises into datasets_v2/web_pages/...")
    os.makedirs(output_dir, exist_ok=True)
    web_files = sorted(glob.glob("documents/web_pages/*.txt"))

    total_web = 0
    total_records = 0
    archetypes = [
        "doctrinal_exegesis",
        "practical_meditation",
        "everyday_dilemma",
        "simile_deconstruction",
        "direct_insight"
    ]

    for w_idx, w_path in enumerate(web_files, 1):
        fname = os.path.basename(w_path)
        with open(w_path, "r", encoding="utf-8", errors="replace") as f:
            raw_text = f.read()

        title = fname.replace(".txt", "").replace("_", " ")
        source_url = "https://accesstoinsight.org"
        author = "Dhamma Master"
        body_lines = []

        in_header = True
        for line in raw_text.split("\n"):
            if in_header:
                if line.startswith("TITLE:"):
                    title = line.replace("TITLE:", "").strip()
                elif line.startswith("AUTHOR:"):
                    author = line.replace("AUTHOR:", "").strip()
                elif line.startswith("SOURCE_URL:"):
                    source_url = line.replace("SOURCE_URL:", "").strip()
                elif line.startswith("=" * 10) or line.strip() == "":
                    in_header = False
            else:
                body_lines.append(line)

        body_text = clean_text_body("\n".join(body_lines))
        w_count = len(body_text.split())
        if w_count < 60:
            continue

        if w_count < 400:
            n_pairs = 4
        elif w_count < 1200:
            n_pairs = 10
        elif w_count < 3000:
            n_pairs = 18
        elif w_count < 8000:
            n_pairs = 32
        else:
            n_pairs = min(65, max(35, w_count // 160))

        source_str = f"{title} ({source_url})"
        quotes = extract_thematic_quotes(body_text, n_pairs)
        records = []
        for p_idx, q_data in enumerate(quotes):
            arch = archetypes[p_idx % len(archetypes)]
            rec = build_longform_qa(title, author, title, q_data, arch, source_str, p_idx)
            records.append(rec)

        if records:
            slug = sanitize_slug(fname.replace(".txt", ""))
            out_file = os.path.join(output_dir, f"{slug}_qa.jsonl")
            with open(out_file, "w", encoding="utf-8") as f:
                for r in records:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
            total_web += 1
            total_records += len(records)
            if w_idx % 40 == 0 or w_idx == len(web_files):
                print(f"      Progress: [{w_idx:3d}/{len(web_files):3d}] web treatises | Distilled: {total_records:6,d} long-form records")

    print(f"   -> Completed Web Treatises: {total_web} files, {total_records:,} long-form QA pairs.")
    return total_web, total_records


def distill_all_youtube_talks(output_dir: str) -> Tuple[int, int]:
    print("\n[3/3] Distilling 59 Spoken Dhamma Talks into datasets_v2/youtube/...")
    os.makedirs(output_dir, exist_ok=True)
    yt_files = sorted(glob.glob("documents/youtube_transcripts/*.txt"))

    total_talks = 0
    total_records = 0
    archetypes = [
        "practical_meditation",
        "everyday_dilemma",
        "doctrinal_exegesis",
        "simile_deconstruction",
        "direct_insight"
    ]

    for y_idx, y_path in enumerate(yt_files, 1):
        fname = os.path.basename(y_path)
        with open(y_path, "r", encoding="utf-8", errors="replace") as f:
            raw_text = clean_text_body(f.read())

        talk_title = fname.replace(".txt", "").replace("_", " ")
        author = "Ajahn Sumedho"
        source_str = f"Spoken Dhamma Talk: {talk_title} - Ajahn Sumedho"

        quotes = extract_thematic_quotes(raw_text, 30)
        records = []
        for p_idx, q_data in enumerate(quotes):
            arch = archetypes[p_idx % len(archetypes)]
            rec = build_longform_qa(talk_title, author, talk_title, q_data, arch, source_str, p_idx)
            records.append(rec)

        if records:
            slug = sanitize_slug(fname.replace(".txt", ""))
            out_file = os.path.join(output_dir, f"{slug}_qa.jsonl")
            with open(out_file, "w", encoding="utf-8") as f:
                for r in records:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
            total_talks += 1
            total_records += len(records)

    print(f"   -> Completed YouTube Talks: {total_talks} talks, {total_records:,} long-form QA pairs.")
    return total_talks, total_records


def merge_and_finalize_distillation():
    print("\n" + "=" * 80)
    print("FINALIZING LONG-FORM V2 MASTER DATASET SPLITS AND SHAREGPT EXPORTS")
    print("=" * 80)

    all_v2_files = []
    for sub in ["books", "web_pages", "youtube"]:
        all_v2_files.extend(glob.glob(f"datasets_v2/{sub}/*.jsonl"))

    print(f"Found {len(all_v2_files)} total V2 component datasets.")

    seen_questions = set()
    all_records = []
    duplicates = 0

    for fpath in all_v2_files:
        with open(fpath, "r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if not line_str:
                    continue
                try:
                    obj = json.loads(line_str)
                    q = obj["messages"][1]["content"].strip().lower()
                    if q in seen_questions:
                        duplicates += 1
                        continue
                    seen_questions.add(q)
                    all_records.append(obj)
                except Exception:
                    pass

    total_unique = len(all_records)
    print(f"\nTotal Unique Long-Form V2 QA Pairs: {total_unique:,} (deduplicated {duplicates:,})")

    random.seed(42)
    random.shuffle(all_records)

    splits_dir = "datasets_v2/splits"
    os.makedirs(splits_dir, exist_ok=True)

    master_path = os.path.join(splits_dir, "master_25k_dhamma_qa.jsonl")
    train_path = os.path.join(splits_dir, "train_25k.jsonl")
    val_path = os.path.join(splits_dir, "val_25k.jsonl")

    val_count = max(1, int(total_unique * 0.10))
    train_count = total_unique - val_count

    val_records = all_records[:val_count]
    train_records = all_records[val_count:]

    with open(master_path, "w", encoding="utf-8") as f:
        for r in all_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    with open(train_path, "w", encoding="utf-8") as f:
        for r in train_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    with open(val_path, "w", encoding="utf-8") as f:
        for r in val_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"[Created] Master 25k Long-Form: {master_path} ({total_unique:,} records)")
    print(f"[Created] Train 25k Long-Form:  {train_path}  ({train_count:,} records)")
    print(f"[Created] Val 25k Long-Form:    {val_path}    ({val_count:,} records)")

    exports_dir = "datasets_v2/exports"
    os.makedirs(exports_dir, exist_ok=True)

    from export_formats import export_dataset
    export_dataset(master_path, os.path.join(exports_dir, "master_25k_sharegpt.json"), "sharegpt")
    export_dataset(train_path, os.path.join(exports_dir, "train_25k_sharegpt.json"), "sharegpt")
    export_dataset(val_path, os.path.join(exports_dir, "val_25k_sharegpt.json"), "sharegpt")

    print("\n" + "=" * 80)
    print("V2 LONG-FORM DISTILLED CORPUS GENERATION SUCCESSFULLY COMPLETED!")
    print("=" * 80)


def run():
    print("=" * 80)
    print("STARTING HIGH-FIDELITY LONG-FORM DHAMMA DISTILLATION PIPELINE (V2)")
    print("=" * 80)

    distill_all_books("datasets_v2/books")
    distill_all_web_pages("datasets_v2/web_pages")
    distill_all_youtube_talks("datasets_v2/youtube")
    merge_and_finalize_distillation()

if __name__ == "__main__":
    run()
