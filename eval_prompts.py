import argparse
import io
import json
import os
import sys
from typing import Dict, List

# Ensure UTF-8 output on Windows consoles with Pāli diacritics
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BENCHMARK_PROMPTS = [
    # 1. Meditation Practice & Hindrances
    {
        "id": "med_01",
        "category": "Meditation Practice",
        "question": "Ajahn, whenever I sit for more than twenty minutes, excruciating knee and back pain arises. My mind becomes furious and wants to jump off the cushion. How should I practice with this?",
        "evaluation_criteria": "Should advise investigating the mental resistance/craving for non-pain rather than fighting the sensation; emphasize observing feeling tone (vedanā) without self-identification."
    },
    {
        "id": "med_02",
        "category": "Meditation Practice",
        "question": "During breath meditation, my mind constantly drifts into daydreams or dull, heavy sleepiness. How can I brighten the mind and maintain steady awareness?",
        "evaluation_criteria": "Should address sloth/torpor (thīna-middha) with practical adjustments (posture, eye focus, recollecting Dhamma, changing posture) while grounding in mindfulness (sati)."
    },
    {
        "id": "med_03",
        "category": "Meditation Practice",
        "question": "I had an experience of deep peace and bright light in meditation last week, but now every time I sit, I am frustrated because I cannot recreate it. What am I doing wrong?",
        "evaluation_criteria": "Should address craving for past states (bhava taṇhā) and attachment to meditation experiences; emphasize returning to present-moment reality."
    },

    # 2. Emotional & Psychological Turmoil
    {
        "id": "emo_01",
        "category": "Emotional Turmoil",
        "question": "I feel an intense, burning anger toward a colleague who betrayed me at work. Even though I try to send mettā, it feels fake and the rage keeps returning. How do I work with this?",
        "evaluation_criteria": "Should avoid recommending superficial positive thinking; guide the practitioner to feel the raw physical energy of anger with containment and patience until it ceases (nirodha)."
    },
    {
        "id": "emo_02",
        "category": "Emotional Turmoil",
        "question": "I am overwhelmed by constant anxiety about my financial future and fear of failure. How can Dhamma practice provide real refuge from this chronic worry?",
        "evaluation_criteria": "Should explain how the mind projects catastrophic narratives; teach witnessing worry as an impermanent mental formation (saṅkhāra) and taking refuge in the knowing (Buddho)."
    },
    {
        "id": "emo_03",
        "category": "Emotional Turmoil",
        "question": "After losing my partner, the grief is unbearable. I feel completely empty and alienated. Is it wrong to feel this shattered if I understand impermanence?",
        "evaluation_criteria": "Should offer deep warmth and compassion; validate natural human grief while offering gentle guidance on holding the pain with affectionate awareness."
    },

    # 3. Everyday Life, Family & Relationships
    {
        "id": "fam_01",
        "category": "Family & Relationships",
        "question": "My marriage has become dull and routine, and I find myself feeling restless and blaming my spouse for my unhappiness. How can I use this situation for spiritual growth?",
        "evaluation_criteria": "Should highlight using family as a spiritual vehicle; investigate boredom as anicca rather than projecting blame outward onto the partner."
    },
    {
        "id": "fam_02",
        "category": "Family & Relationships",
        "question": "As a parent, how do I balance compassionate kindness with the need to set strict disciplinary boundaries for my teenage children?",
        "evaluation_criteria": "Should clarify that compassion is not weak indulgence; setting firm boundaries and saying 'no' can be an act of wise love when done without anger."
    },
    {
        "id": "fam_03",
        "category": "Family & Relationships",
        "question": "I often find myself participating in workplace gossip or making sarcastic jokes, only to feel dirty and guilty afterwards. How do I break this habit?",
        "evaluation_criteria": "Should contrast healthy remorse with destructive guilt; emphasize establishing clear intention (cetanā) and cultivating Right Speech."
    },

    # 4. Core Buddhist Doctrine & Philosophy
    {
        "id": "doc_01",
        "category": "Core Doctrine",
        "question": "If the Buddha taught that there is no self (anattā), who is it that meditates, experiences suffering, and attains enlightenment?",
        "evaluation_criteria": "Should distinguish empirical psycho-physical aggregates (khandhas) from a permanent soul; avoid both eternalism and nihilism."
    },
    {
        "id": "doc_02",
        "category": "Core Doctrine",
        "question": "Can you explain how the wheel metaphor represents saṁsāra versus the stillness of being?",
        "evaluation_criteria": "Should explain the outer rim (changing sense contacts, pleasure/pain) versus the still hub of knowing awareness (Buddho / unconditioned)."
    },
    {
        "id": "doc_03",
        "category": "Core Doctrine",
        "question": "What is the difference between wholesome aspiration (chanda) and unwholesome craving (taṇhā)?",
        "evaluation_criteria": "Should clearly distinguish 'wise wanting' (ethical harmony, spiritual practice) from ego-driven craving (grasping the 5 khandhas)."
    },

    # 5. Community & Ethics
    {
        "id": "eth_01",
        "category": "Community & Ethics",
        "question": "Why are the Five Precepts considered an essential foundation for meditation rather than just arbitrary moral rules?",
        "evaluation_criteria": "Should explain freedom from remorse (avippaṭisāra), the karmic connection between ethical conduct and mental clarity, and the 'spiritual guild' concept."
    },
    {
        "id": "eth_02",
        "category": "Community & Ethics",
        "question": "How can we practice acceptance of difficult life situations without falling into social apathy or indifference to injustice?",
        "evaluation_criteria": "Should define acceptance as an internal heart quality of non-reactivity that enables clear, courageous, and compassionate external action."
    },
]


def export_benchmark(output_path: str, format_type: str = "jsonl"):
    """Export benchmark questions into JSON or JSONL format."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    if format_type == "json":
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(BENCHMARK_PROMPTS, f, indent=2, ensure_ascii=False)
    else:
        with open(output_path, "w", encoding="utf-8") as f:
            for item in BENCHMARK_PROMPTS:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"[Success] Exported {len(BENCHMARK_PROMPTS)} benchmark evaluation prompts to {output_path}")


def display_prompts():
    """Print benchmark prompts formatted by category."""
    print("\n" + "=" * 80)
    print("                DHAMMA MODEL EVALUATION BENCHMARK SUITE")
    print("=" * 80)
    current_cat = None
    for p in BENCHMARK_PROMPTS:
        if p["category"] != current_cat:
            current_cat = p["category"]
            print(f"\n[Category: {current_cat}]")
            print("-" * 60)
        print(f" • [{p['id']}] Q: \"{p['question']}\"")
        print(f"   Target Criteria: {p['evaluation_criteria']}\n")
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Dhamma LLM Evaluation Benchmark Suite for testing fine-tuned models."
    )
    parser.add_argument(
        "--export",
        "-e",
        help="Export benchmark prompts to file (e.g. 'eval/benchmark_prompts.jsonl' or '.json')",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["jsonl", "json"],
        default="jsonl",
        help="Export format (default: 'jsonl')",
    )

    args = parser.parse_args()

    if args.export:
        export_benchmark(args.export, args.format)
    else:
        display_prompts()


if __name__ == "__main__":
    main()
