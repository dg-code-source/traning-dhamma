#!/usr/bin/env python3
"""
tools/web_page_pipeline.py — Web Page → Training Data Pipeline

Fetches one or more web pages (e.g. dhammatalks.org book sections),
extracts the main teaching text, generates transcript-grounded QA pairs
using the same Thai Forest 4-part structure, saves per-page JSONL datasets,
and rebuilds the master train/val splits.

Usage
─────
# Add & process a single URL
python tools/web_page_pipeline.py --add https://www.dhammatalks.org/books/HeartReleased/Section0005.html

# Add multiple URLs at once
python tools/web_page_pipeline.py --add URL1 URL2 URL3 ...

# Process from a text file (one URL per line)
python tools/web_page_pipeline.py --file urls.txt

# List all registered web pages
python tools/web_page_pipeline.py --list

# Check if a URL has already been processed
python tools/web_page_pipeline.py --check https://...

# Reprocess a specific URL (re-fetch + re-generate)
python tools/web_page_pipeline.py --reprocess https://...

# Status report
python tools/web_page_pipeline.py --status
"""

import os, sys, json, re, hashlib, argparse, time, urllib.request, urllib.error, urllib.parse, io
from typing import List, Tuple, Optional
from html.parser import HTMLParser

try:
    import pypdf
except ImportError:
    pypdf = None

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ── Paths ────────────────────────────────────────────────────────────────────
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WEB_DIR = os.path.join(ROOT_DIR, "documents", "web_pages")
WEB_DS_DIR = os.path.join(ROOT_DIR, "datasets", "web_pages")
MASTER_DS_DIR = os.path.join(ROOT_DIR, "datasets")
REGISTRY_FILE = os.path.join(WEB_DIR, "web_registry.json")

os.makedirs(WEB_DIR, exist_ok=True)
os.makedirs(WEB_DS_DIR, exist_ok=True)
os.makedirs(MASTER_DS_DIR, exist_ok=True)

# ── System prompt ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = (
    "You are a wise and compassionate Dhamma teacher grounded in the Thai Forest "
    "Tradition (in the lineage of Luang Por Chah). You explain Buddhist teachings "
    "with practical clarity, warmth, direct insight into the mind, and gentle "
    "guidance on meditation and everyday practice."
)

# ── Pāli concept map ─────────────────────────────────────────────────────────
PALI_MAP = {
    "anicca": ("anicca", "impermanence (anicca) — all conditioned phenomena arise and pass away"),
    "inconstancy": ("anicca", "impermanence (anicca) — the ever-changing nature of experience"),
    "impermanent": ("anicca", "impermanence (anicca)"),
    "dukkha": ("dukkha", "stress/suffering (dukkha) — the unsatisfactoriness of conditioned existence"),
    "stress": ("dukkha", "stress (dukkha) — the first noble truth"),
    "suffering": ("dukkha", "suffering (dukkha)"),
    "anatta": ("anattā", "not-self (anattā) — no fixed, independent self exists anywhere"),
    "not-self": ("anattā", "not-self (anattā)"),
    "not-selfness": ("anattā", "not-selfness (anattā)"),
    "sati": ("sati", "mindfulness (sati) — clear, present-moment awareness"),
    "mindfulness": ("sati", "mindfulness (sati)"),
    "samadhi": ("samādhi", "concentration (samādhi) — the unified, still mind"),
    "concentration": ("samādhi", "concentration (samādhi)"),
    "jhana": ("jhāna", "meditative absorption (jhāna)"),
    "jhāna": ("jhāna", "meditative absorption (jhāna) — deep states of collected stillness"),
    "panna": ("paññā", "discernment/wisdom (paññā) — direct insight into the nature of experience"),
    "discernment": ("paññā", "discernment (paññā)"),
    "wisdom": ("paññā", "wisdom (paññā)"),
    "sila": ("sīla", "virtue/moral restraint (sīla)"),
    "virtue": ("sīla", "virtue (sīla) — the foundation of the path"),
    "precept": ("sīla", "the precepts (sīla) — training rules that protect the mind"),
    "cetana": ("cetanā", "intention (cetanā) — the volition that forms the essence of virtue"),
    "intention": ("cetanā", "intention (cetanā) — the willed action behind all conduct"),
    "kamma": ("kamma", "intentional action (kamma) and its fruits"),
    "karma": ("kamma", "kamma — volitional action shaping future experience"),
    "nibbana": ("Nibbāna", "Nibbāna — the unconditioned, the cessation of all craving"),
    "nirvana": ("Nibbāna", "Nibbāna — the deathless peace beyond conditioned existence"),
    "akaliko": ("akāliko", "ever-present (akāliko) — the Dhamma exists at all times, not just in certain seasons"),
    "opanayiko": ("opanayiko", "leading inward (opanayiko) — the invitation to turn teachings into direct investigation"),
    "paccattam": ("paccattaṁ", "to be known individually (paccattaṁ) — the Dhamma is verified by each practitioner for themselves"),
    "nimitta": ("nimitta", "meditative sign (nimitta) — an image arising in deep concentration"),
    "uggaha nimitta": ("uggaha nimitta", "arising image (uggaha nimitta) — first nimitta in body-contemplation"),
    "patibhaga": ("paṭibhāga nimitta", "counterpart image (paṭibhāga nimitta) — refined, stable nimitta"),
    "vipassana": ("vipassanā", "insight meditation (vipassanā) — direct seeing of the three characteristics"),
    "dhamma-vicaya": ("dhamma-vicaya", "analysis of phenomena (dhamma-vicaya) — one of the seven factors of Awakening"),
    "bojjhanga": ("bojjhaṅga", "factors of Awakening (bojjhaṅgas) — seven mental qualities leading to liberation"),
    "satipatthana": ("satipaṭṭhāna", "establishments of mindfulness (satipaṭṭhānas)"),
    "metta": ("mettā", "loving-kindness (mettā) — boundless goodwill toward all beings"),
    "karuna": ("karuṇā", "compassion (karuṇā) — the wish to relieve suffering"),
    "arahant": ("arahant", "a fully awakened being (arahant) who has eradicated all defilements"),
    "dhamma": ("Dhamma", "the Dhamma — the truth, the teaching, the nature of reality"),
    "vinaya": ("Vinaya", "the Vinaya — the code of monastic discipline"),
    "tanha": ("taṇhā", "craving (taṇhā) — the thirst driving the cycle of suffering"),
    "kilesa": ("kilesa", "defilements (kilesas) — mental impurities that obscure the mind"),
    "defilement": ("kilesa", "defilements (kilesas)"),
    "rupa": ("rūpa", "form/body (rūpa) — the physical dimension of experience"),
    "vedana": ("vedanā", "feeling-tone (vedanā) — pleasant, unpleasant, or neutral quality of experience"),
    "sankhara": ("saṅkhāra", "formations (saṅkhāras) — conditioned mental and physical phenomena"),
    "vinnana": ("viññāna", "consciousness (viññāna) — the knowing aspect of mind"),
    "five aggregates": ("khandha", "the five aggregates (khandhas) — form, feeling, perception, formations, consciousness"),
    "forest": ("araññavāsi", "the Forest Tradition — monks practising in wilderness solitude"),
    "preceptor": ("upajjhāya", "preceptor (upajjhāya) — the senior monk who ordains and guides a new monk"),
}


# ══════════════════════════════════════════════════════════════════════════════
# HTML → Clean Text Extractor
# ══════════════════════════════════════════════════════════════════════════════

class DhammaHTMLParser(HTMLParser):
    """Extract structured text from dhammatalks.org-style pages."""

    # Void/self-closing tags that have no matching end tag in HTML
    VOID_TAGS = {"meta", "link", "img", "br", "hr", "input"}
    # Container elements whose inner content should be skipped
    SKIP_TAGS = {"script", "style", "noscript", "button", "svg", "path"}
    BLOCK_TAGS = {"p", "h1", "h2", "h3", "h4", "li", "br",
                  "blockquote", "section", "article"}

    def __init__(self):
        super().__init__()
        self.paragraphs: List[str] = []
        self.headings: List[Tuple[str, str]] = []  # (level, text)
        self._skip_depth = 0
        self._main_depth = 0   # >0 when inside <main> or #content
        self._in_quote = False
        self._tag_stack: List[str] = []
        self._current_buf: List[str] = []
        self._current_heading: Optional[str] = None
        self.title = ""
        self._in_title = False

    def _flush_buf(self):
        text = " ".join(self._current_buf).strip()
        text = re.sub(r"\s+", " ", text)
        if text and len(text.split()) >= 4:
            self.paragraphs.append(text)
        self._current_buf = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag not in self.VOID_TAGS:
            self._tag_stack.append(tag)

        # Detect entry into main content area
        tag_id = attrs_dict.get("id", "").lower()
        tag_class = attrs_dict.get("class", "").lower()
        
        # Stop collecting when reaching footer sections
        if "f_footer" in tag_id or "f_colophon" in tag_id or "f_provenance" in tag_id or tag in ("footer",):
            self._skip_depth += 1
            return

        is_main_entry = (
            tag in ("main", "article", "body") or 
            any(k in tag_id for k in ("content", "h_content", "main-content", "truth", "body", "copyrighted_text")) or
            any(k in tag_class for k in ("content", "main-content", "entry-content", "post-content"))
        )

        if is_main_entry and self._main_depth == 0:
            self._main_depth = len(self._tag_stack)  # mark stack level where main started


        if tag == "title":
            self._in_title = True

        if tag in self.SKIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth > 0:
            return

        # Skip nav/header before main starts
        if tag in ("nav", "header") and self._main_depth == 0:
            self._skip_depth += 1
            return

        if self._main_depth == 0:
            return  # Don't collect anything outside main

        if tag in ("h1", "h2", "h3", "h4"):
            self._flush_buf()
            self._current_heading = tag

        elif tag in self.BLOCK_TAGS:
            self._flush_buf()

        if tag_class == "quote" or tag_id == "quote":
            self._in_quote = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

        if tag in self.SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)

        if tag in ("nav", "header", "footer") and self._skip_depth > 0:
            self._skip_depth = max(0, self._skip_depth - 1)

        if self._main_depth > 0:
            if tag in self.BLOCK_TAGS or tag in ("div", "main", "article"):
                self._flush_buf()
            # If we've popped back above the level where main started, reset main_depth
            if len(self._tag_stack) <= self._main_depth:
                self._main_depth = 0

        if self._tag_stack and self._tag_stack[-1] == tag:
            self._tag_stack.pop()



    def handle_data(self, data):
        text = data.strip()
        if not text:
            return

        if self._in_title and not self.title:
            self.title = text
            return

        if self._skip_depth > 0:
            return

        if self._main_depth == 0:
            return

        if self._current_heading:
            self._current_buf.append(f"[Section: {text}]")
            self._current_heading = None
        else:
            self._current_buf.append(text)

    def get_text(self) -> str:
        self._flush_buf()
        return "\n".join(self.paragraphs)


def fetch_raw_bytes(url: str, retries: int = 3, delay: float = 2.0) -> Tuple[bytes, str]:
    """Fetch raw bytes and content-type from URL with retry logic."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,application/pdf,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive"
    }
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=45) as resp:
                raw = resp.read()
                ct = resp.getheader("Content-Type", "")
                return raw, ct
        except urllib.error.HTTPError as e:
            print(f"  HTTP {e.code} on attempt {attempt+1}: {url}")
        except Exception as e:
            print(f"  Fetch error on attempt {attempt+1}: {e}")
        if attempt < retries - 1:
            time.sleep(delay * (attempt + 1))
    raise RuntimeError(f"Failed to fetch: {url}")


def fetch_url(url: str, retries: int = 3, delay: float = 2.0) -> str:
    """Fetch raw HTML/text from URL with retry logic."""
    raw, ct = fetch_raw_bytes(url, retries=retries, delay=delay)
    enc = "utf-8"
    m = re.search(r"charset=([^\s;]+)", ct)
    if m:
        enc = m.group(1)
    return raw.decode(enc, errors="replace")


def extract_pdf_content(pdf_bytes: bytes, url: str) -> Tuple[str, str]:
    """Extract (title, clean_body_text) from PDF bytes."""
    if pypdf is None:
        raise RuntimeError("pypdf is not installed. Run: pip install pypdf")

    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    meta = reader.metadata or {}
    title = meta.get("/Title")
    if not title or str(title).strip() in ("", "Untitled"):
        base_name = os.path.splitext(os.path.basename(urllib.parse.urlparse(url).path))[0]
        title = base_name.replace("_", " ").replace("-", " ").strip()
    title = str(title).strip()

    pages_text = []
    for page in reader.pages:
        try:
            t = page.extract_text() or ""
            # Clean common artifacts
            t = re.sub(r"(\w+)-\n(\w+)", r"\1\2", t)
            t = re.sub(r"\n\s*\d+\s*\n", "\n\n", t)
            pages_text.append(t.strip())
        except Exception:
            continue

    body = "\n\n".join([p for p in pages_text if p])
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    return title, body



def extract_clean_text(html: str) -> Tuple[str, str]:
    """Return (title, clean_body_text) from raw HTML."""
    parser = DhammaHTMLParser()
    parser.feed(html)
    raw = parser.get_text()
    title = parser.title or ""

    # Clean up page title (remove site name suffix)
    title = re.sub(r"\s*\|\s*ebook on dhammatalks\.org\s*$", "", title).strip()

    # Collapse multiple blank lines
    body = re.sub(r"\n{3,}", "\n\n", raw).strip()
    return title.strip(), body


# ══════════════════════════════════════════════════════════════════════════════
# QA Generation (same Thai Forest 4-part structure)
# ══════════════════════════════════════════════════════════════════════════════

def detect_pali_terms(text_lower: str) -> List[Tuple[str, str]]:
    found = {}
    for keyword, (pali, gloss) in PALI_MAP.items():
        if keyword in text_lower:
            found[pali] = gloss
    return list(found.items())[:8]


def extract_key_passages(text: str, n: int = 20) -> List[str]:
    """Pull teaching-rich sentences from the text."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    teaching_markers = [
        "contemplate", "meditat", "awareness", "mindful", "virtue", "discernment",
        "wisdom", "practice", "training", "defilement", "craving", "concentration",
        "jhana", "nibbana", "dhamma", "buddha", "release", "suffering", "stress",
        "impermanent", "anicca", "not-self", "truth", "nature", "observe",
        "investigate", "insight", "sati", "kilesa", "let go", "cessation",
        "liberation", "awakening", "purity", "clear", "knowing", "body", "mind",
        "heart", "precept", "breath", "inconstant", "ever-present", "akāliko",
    ]
    scored = []
    for s in sentences:
        s = s.strip()
        if len(s.split()) < 8 or len(s.split()) > 100:
            continue
        sl = s.lower()
        score = sum(1 for m in teaching_markers if m in sl)
        if score > 0:
            scored.append((score, s))
    scored.sort(reverse=True)
    seen = set()
    out = []
    for _, s in scored:
        key = s[:40]
        if key not in seen:
            seen.add(key)
            out.append(s)
        if len(out) >= n:
            break
    return out


def extract_named_sections(text: str) -> List[Tuple[str, str]]:
    """Extract [Section: X] blocks with their content."""
    sections = []
    parts = re.split(r"\[Section: ([^\]]+)\]", text)
    for i in range(1, len(parts), 2):
        sec_title = parts[i].strip()
        sec_body = parts[i+1].strip() if i+1 < len(parts) else ""
        if sec_body:
            sections.append((sec_title, sec_body[:600]))
    return sections


def build_qa_pairs(page_title: str, url: str, body: str) -> List[Tuple[str, str]]:
    """Generate transcript-grounded QA pairs from a web page body."""
    tl = body.lower()
    pali_terms = detect_pali_terms(tl)
    key_passages = extract_key_passages(body, n=25)
    named_sections = extract_named_sections(body)
    word_count = len(body.split())
    target_count = min(15, max(8, word_count // 200))

    # Clean display title (remove site name suffix)
    clean_title = re.sub(r"\s*\|.*$", "", page_title).strip()
    if not clean_title:
        clean_title = "this Dhamma teaching"

    pairs = []
    used = set()

    # ── Pair 1: Opening overview ─────────────────────────────────────────────
    # Find the first substantive sentence from the actual body text
    all_sentences = re.split(r"(?<=[.!?])\s+", body)
    opening = ""
    for s in all_sentences:
        s = s.strip()
        # Strip any inline [Section: X] markers
        s = re.sub(r"\[Section:[^\]]*\]\s*", "", s).strip()
        if len(s.split()) < 10:
            continue
        opening = s
        break
    if not opening:
        opening = re.sub(r"\[Section:[^\]]*\]\s*", "", body[:300]).strip()


    pairs.append((
        f"What is the essential teaching in '{clean_title}'?",
        f"In '{clean_title}', the teaching opens with this observation: "
        f"*\"{opening.rstrip()}\"* "
        f"The central invitation is to turn one's investigation inward — "
        f"to verify the Dhamma not as a set of beliefs, but as directly observable reality "
        f"in one's own body, speech, and mind. "
        f"As the text teaches, the Dhamma is *akāliko* — ever-present — and *opanayiko* — "
        f"leading inward — available to be known (*paccattaṁ*) by each practitioner for themselves. "
        f"There is no need to search elsewhere; the truth is already here."
    ))
    used.add("overview")


    # ── Pairs from named sections ─────────────────────────────────────────────
    for sec_title, sec_body in named_sections[:6]:
        stl = sec_title.lower()
        key = sec_title[:20]
        if key in used:
            continue
        used.add(key)

        if any(w in stl for w in ["virtue", "sila", "precept"]):
            pairs.append((
                f"The section on '{sec_title}' says virtue is like rock. How does this understanding change our practice?",
                f"In this section, the teaching on virtue (sīla) states: *\"{sec_body[:250]}...\"* "
                f"Virtue is not something we receive from outside by asking for precepts; "
                f"it is the natural quality of a mind that guards itself through intention (cetanā). "
                f"The simile of rock points to sīla as the solid, unmovable foundation — "
                f"not shaken by circumstances, opinions, or moods. "
                f"When we recognise that virtue already dwells in our own body-speech-mind, "
                f"we stop searching outward and start tending the quality of our own intentions."
            ))
        elif any(w in stl for w in ["concentrat", "jhana", "samadhi", "purify", "mind"]):
            pairs.append((
                f"How does the teaching in '{sec_title}' guide the development of samādhi?",
                f"The text instructs: *\"{sec_body[:300]}...\"* "
                f"Three progressive levels of concentration (samādhi) are described: "
                f"momentary (the mind briefly settles and withdraws), threshold (the mind "
                f"rests at its underlying level for a sustained period), and fixed penetration "
                f"(the mind abides in full jhāna, endowed with the five jhāna factors). "
                f"Samādhi is not forced; it arises naturally when mindfulness (sati) and "
                f"investigation (dhamma-vicaya) reach sufficient momentum. "
                f"Sit quietly now and simply watch the breath — notice when the mind settles, even briefly."
            ))
        elif any(w in stl for w in ["body", "contemplate", "physical", "death"]):
            pairs.append((
                f"Why does '{sec_title}' place such emphasis on contemplating the body?",
                f"The text teaches: *\"{sec_body[:300]}...\"* "
                f"Body contemplation (kāyagatāsati) is the Buddha's own recommended entry point "
                f"because the body is always with us and plainly reveals the three characteristics: "
                f"it is impermanent (anicca), involves stress (dukkha), and is not a self (anattā). "
                f"Beginning with the five meditation themes — hair of head, hair of body, nails, teeth, skin — "
                f"the practitioner trains the eye of discernment (paññā) to see through the illusion of beauty "
                f"and find the inherent truth beneath. "
                f"Right now, bring gentle attention to the feel of your body sitting — notice it is always changing."
            ))
        elif any(w in stl for w in ["truth", "ever-present", "principle"]):
            pairs.append((
                f"What does it mean that 'the principles of the practice are ever-present', as taught in '{sec_title}'?",
                f"*\"{sec_body[:300]}...\"* "
                f"The Pāli term *akāliko* — timeless, ever-present — applies to Dhamma itself. "
                f"This means the truth of impermanence, suffering, and not-self is observable "
                f"in this very moment, not only during formal meditation. "
                f"A leaf falling from a tree shows impermanence; a mood arising and dissolving shows dukkha; "
                f"the absence of a fixed 'experiencer' behind experience shows anattā. "
                f"The practice is therefore not a project for the future — it is available right now, "
                f"wherever you are, at all times."
            ))
        elif any(w in stl for w in ["listen", "dhamma", "hearing"]):
            pairs.append((
                f"The section '{sec_title}' describes listening to the Dhamma at all times. How does one practise this?",
                f"The teaching explains: *\"{sec_body[:300]}...\"* "
                f"'Listening to the Dhamma at all times' (sato sampajāno) means using every sensory "
                f"encounter as an object of mindful investigation. The eye sees form — note impermanence. "
                f"The ear hears sound — note how it arises and passes. The mind encounters a thought — "
                f"note how it dissolves without being held. Every moment is a Dhamma talk being given "
                f"by reality itself. The practitioner's task is to stay awake, curious, and non-reactive — "
                f"receiving the continuous teaching without grasping or rejecting."
            ))
        elif any(w in stl for w in ["potential", "associate", "sage"]):
            pairs.append((
                f"What is the significance of 'potential' (barami) in the context of '{sec_title}'?",
                f"The text observes: *\"{sec_body[:250]}...\"* "
                f"Our potential (pāramī) — the accumulated spiritual qualities from past cultivation — "
                f"is not fixed. It is shaped by who we associate with and how we direct our attention. "
                f"The Buddha consistently praised the kalyāṇamitta (spiritual friend) as the entire holy life. "
                f"Associating with those who embody wisdom, virtue, and clarity lifts our own potential; "
                f"association with the heedless diminishes it. "
                f"Choose your companions, teachers, and reading material with care — they shape the mind."
            ))
        else:
            pairs.append((
                f"Can you explain the teaching in the section '{sec_title}'?",
                f"This section teaches: *\"{sec_body[:350]}...\"* "
                f"The core instruction is to turn investigation inward (*opanayiko*) toward what is "
                f"already present in body, speech, and mind — not to seek the Dhamma outside or in future states. "
                f"Whatever theme this section addresses, the method is the same: "
                f"sustained, patient, non-grasping awareness that allows the truth to reveal itself. "
                f"As Ajahn Mun taught: when the mind sees clearly, there is no longer any need to go looking."
            ))

        if len(pairs) >= target_count:
            break

    # ── Pairs from detected Pāli terms ───────────────────────────────────────
    for pali, gloss in pali_terms:
        if len(pairs) >= target_count:
            break
        key = pali.lower()[:8]
        if key in used:
            continue
        used.add(key)

        # Find a sentence in the text that mentions this concept
        term_sentence = ""
        # Build variants: original pali word + ascii-folded version
        pali_first = pali.split()[0]
        ascii_pali = pali_first.lower()
        for ch, rep in [("ā","a"),("ī","i"),("ū","u"),("ṃ","m"),("ṅ","n"),
                        ("ñ","n"),("ṭ","t"),("ḍ","d"),("ṇ","n"),("ḷ","l")]:
            ascii_pali = ascii_pali.replace(ch, rep)
        # Get all raw sentences from body
        raw_sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", body)
                     if 8 <= len(s.split()) <= 80 and not s.strip().startswith("[Section:")]
        for sent in raw_sents:
            sl = sent.lower()
            if ascii_pali in sl or pali_first.lower() in sl or \
               any(kw in sl for kw in gloss.lower().split()[:3]):
                term_sentence = sent[:200]
                break


        if "akālik" in pali.lower() or "akālik" in gloss.lower():
            pairs.append((
                "What does the Pāli term 'akāliko' mean and why does it matter for practice?",
                f"In this text, akāliko appears in the context: *\"{term_sentence or 'the Dhamma is akāliko — ever-present.'}\"* "
                f"Akāliko means 'not time-bound' or 'ever-present.' It is one of the six qualities of the Dhamma "
                f"recited in the Dhamma-vandanā (homage to the Dhamma): "
                f"svākkhāto (well-proclaimed), sandiṭṭhiko (visible here and now), akāliko (timeless), "
                f"ehipassiko (inviting investigation), opanayiko (leading inward), paccattaṁ veditabbo viññūhi "
                f"(to be known individually by the wise). "
                f"Akāliko means the truth of impermanence, suffering, and not-self is not seasonal — "
                f"it is observable right now, in this breath, this feeling, this moment."
            ))
        elif "jhā" in pali.lower():
            pairs.append((
                f"This text describes jhāna and meditation levels. What are the key stages?",
                f"The text teaches: *\"{term_sentence or 'the mind settles into jhāna when mindfulness is sufficiently developed.'}\"* "
                f"Three levels of concentration are distinguished: "
                f"(1) momentary concentration — the mind briefly settles then withdraws; "
                f"(2) threshold concentration — the mind rests at its underlying level for a sustained time, "
                f"often accompanied by a nimitta (sign); "
                f"(3) fixed penetration (appanā samādhi) — full jhāna, where the mind abides in "
                f"deep stillness endowed with applied thought, sustained thought, rapture, pleasure, and unification. "
                f"Each level is a stepping stone; none should be forced. "
                f"Develop mindfulness, and samādhi will arise of its own accord like water finding its level."
            ))
        elif "nimitta" in pali.lower():
            pairs.append((
                "What is a nimitta and how should a meditator work with it?",
                f"The text refers to nimitta in this way: *\"{term_sentence or 'a nimitta arises in deep concentration.'}\"* "
                f"A nimitta is a meditative sign — an image or sensation that arises when the mind gathers "
                f"into threshold or fixed concentration. The uggaha nimitta (arising image) is the first form; "
                f"the paṭibhāga nimitta (counterpart image) is the cleaner, more refined form used to deepen jhāna. "
                f"The instruction is not to grasp at the nimitta or become excited by it, but to continue "
                f"contemplating calmly until the mind naturally settles deeper. "
                f"Nimittas are tools, not goals — the goal is insight into the three characteristics."
            ))
        else:
            pairs.append((
                f"This text mentions {gloss.split('—')[0].strip()}. Can you explain its role in practice?",
                f"In this text, {pali} appears in this context: *\"{term_sentence or 'the teaching points to ' + pali + ' as a central quality.'}\"* "
                f"Understanding {gloss} is not merely conceptual — it is meant to be verified directly. "
                f"The Dhamma is *ehipassiko*: 'come and see for yourself.' "
                f"Bring the quality described by {pali} into direct investigation: "
                f"where is it present in your current experience? "
                f"When seen clearly, each of these Pāli terms dissolves from abstract concept into living reality."
            ))

    # ── Fill remaining from key passages ─────────────────────────────────────
    for sent in key_passages:
        if len(pairs) >= target_count:
            break
        sl = sent.lower()
        key = sent[:30]
        if key in used:
            continue
        used.add(key)

        if any(w in sl for w in ["preceptor", "ordination", "ordain", "monk"]):
            pairs.append((
                "Why does the preceptor teach the five meditation themes at ordination?",
                f"The text explains: *\"{sent}\"* "
                f"The five themes — hair of head (kesā), hair of body (lomā), nails (nakhā), "
                f"teeth (dantā), skin (taco) — are not arbitrary. They target the root of infatuation "
                f"with the body. The skin, as the outermost layer, is what we are actually attracted to "
                f"when we conceive of a body as beautiful. Contemplating the skin as a wrapping "
                f"that holds together otherwise repulsive components directly undercuts sensual desire. "
                f"This is the very first teaching given to a new monk — showing that the entire path "
                f"begins with honest, unflinching investigation of the body."
            ))
        elif "studied a lot" in sl or "learning" in sl or "scholarly" in sl:
            pairs.append((
                "How should someone who has studied a great deal of Dhamma approach meditation?",
                f"The text cautions: *\"{sent}\"* "
                f"Those who have accumulated much doctrinal knowledge often find their minds restless "
                f"and difficult to settle in formal meditation. The instruction is to 'put the learning "
                f"back on the shelf for the time being' and train 'what knows' — the bare awareness itself. "
                f"Intellectual understanding is valuable as a map, but the map is not the territory. "
                f"Mindfulness must eventually move past conceptual overlays into direct, non-verbal knowing. "
                f"Let the books rest. Sit quietly and simply notice what is arising and passing."
            ))
        elif any(w in sl for w in ["confused", "look for", "searching"]):
            pairs.append((
                "The teaching says a confused person keeps searching while a clear person stays with what is present. What does this mean in practice?",
                f"The text observes: *\"{sent}\"* "
                f"This points to the paradox of spiritual seeking: the very act of restless searching "
                f"presupposes that what we are looking for is absent. But the Dhamma is akāliko — "
                f"already here, already present in the body, feelings, and the aware mind itself. "
                f"Confusion is movement; clarity is stillness. "
                f"When you stop adding to experience and simply rest in what is already present — "
                f"breath, body weight, sounds, the bare fact of awareness — the search naturally ends. "
                f"Not because you found something new, but because you stopped covering what was always here."
            ))

    return pairs[:target_count]


# ══════════════════════════════════════════════════════════════════════════════
# Registry Management
# ══════════════════════════════════════════════════════════════════════════════

def load_registry() -> dict:
    if os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"pages": []}


def save_registry(reg: dict):
    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(reg, f, indent=2, ensure_ascii=False)


def url_slug(url: str) -> str:
    """Deterministic short slug from URL."""
    # Use last path component + short hash
    path = re.sub(r"https?://[^/]+", "", url).strip("/")
    path_clean = re.sub(r"[^a-z0-9]+", "_", path.lower())[:60]
    hx = hashlib.md5(url.encode()).hexdigest()[:6]
    return f"web_{path_clean}_{hx}"


def find_page_entry(reg: dict, url: str) -> Optional[dict]:
    for entry in reg.get("pages", []):
        if entry["url"] == url:
            return entry
    return None


def extract_toc_links(html: str, base_url: str) -> List[str]:
    """Extract ordered section/chapter links from a book index page or TOC."""
    toc_links = []
    
    # 1. Look for explicit Table of Contents blocks (e.g., dhammatalks.org accordion or toc-nav)
    patterns = [
        r'class=["\'][^"\']*book-toc[^"\']*["\']>(.*?)</div>\s*</div>',
        r'class=["\'][^"\']*(?:toc-nav|table-of-contents|book-contents)[^"\']*["\']>(.*?)</ul>',
        r'<nav[^>]*id=["\'](?:bookToc|toc)[^>]*>(.*?)</nav>',
    ]
    
    for pat in patterns:
        m = re.search(pat, html, re.DOTALL | re.IGNORECASE)
        if m:
            block = m.group(1)
            raw_hrefs = re.findall(r'href=["\']([^#"\'\s]+)["\']', block)
            for href in raw_hrefs:
                if href.lower().endswith((".html", ".htm", "/")):
                    full = urllib.parse.urljoin(base_url, href)
                    if full not in toc_links:
                        toc_links.append(full)
            if toc_links:
                break

    # 2. Fallback: Search the full HTML for relative section links if no TOC container matched
    if not toc_links:
        raw_hrefs = re.findall(r'href=["\']([^#"\'\s]*(?:Section|\d+|chapter)[^#"\'\s]*\.html?)["\']', html, re.IGNORECASE)
        for href in raw_hrefs:
            full = urllib.parse.urljoin(base_url, href)
            if full not in toc_links:
                toc_links.append(full)

    return toc_links


# ══════════════════════════════════════════════════════════════════════════════
# Core Processing
# ══════════════════════════════════════════════════════════════════════════════


def process_url(url: str, force: bool = False, min_words: int = 150) -> dict:
    """Fetch, extract, generate QA, and save dataset for one URL."""
    reg = load_registry()
    existing = find_page_entry(reg, url)

    if existing and existing.get("status") == "COMPLETED" and not force:
        print(f"  [SKIP] Already completed: {url}")
        print(f"         Dataset: {existing.get('dataset_file')}")
        return existing

    print(f"\n  Fetching: {url}")
    is_pdf = url.lower().endswith(".pdf")
    try:
        if is_pdf:
            raw_bytes, ct = fetch_raw_bytes(url)
            print(f"  Extracting text from PDF ({len(raw_bytes):,} bytes)...")
            title, body = extract_pdf_content(raw_bytes, url)
        else:
            raw_bytes, ct = fetch_raw_bytes(url)
            # Check if content type indicates PDF despite URL
            if "application/pdf" in ct.lower():
                print(f"  Extracting text from PDF ({len(raw_bytes):,} bytes)...")
                title, body = extract_pdf_content(raw_bytes, url)
            else:
                enc = "utf-8"
                m = re.search(r"charset=([^\s;]+)", ct)
                if m:
                    enc = m.group(1)
                html = raw_bytes.decode(enc, errors="replace")
                print(f"  Extracting text from HTML...")
                title, body = extract_clean_text(html)
    except RuntimeError as e:
        print(f"  [ERROR] {e}")
        entry = existing or {"url": url, "slug": url_slug(url)}
        entry["status"] = "ERROR"
        entry["error"] = str(e)
        _upsert_entry(reg, entry)
        save_registry(reg)
        return entry

    if not title:
        title = url.split("/")[-1].replace(".html", "").replace(".pdf", "").replace("_", " ").replace("-", " ").title()

    word_count = len(body.split())
    print(f"  Title: {title} | {word_count} words")


    if word_count < min_words:
        print(f"  [SKIP] Word count ({word_count}) below minimum ({min_words} words) — likely a cover/titlepage/nav page.")
        entry = existing or {"url": url, "slug": url_slug(url)}
        entry.update({
            "url": url,
            "title": title,
            "status": "SKIPPED_TOO_SHORT",
            "word_count": word_count,
            "qa_count": 0,
            "processed_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        })
        _upsert_entry(reg, entry)
        save_registry(reg)
        return entry

    # Save raw text
    slug = url_slug(url)
    text_file = os.path.join(WEB_DIR, f"{slug}.txt")
    with open(text_file, "w", encoding="utf-8") as f:
        f.write(f"Title: {title}\nURL: {url}\nWord Count: {word_count}\n\n")
        f.write(body)
    print(f"  Saved text: {os.path.basename(text_file)}")

    print(f"  Generating QA pairs...")
    qa_pairs = build_qa_pairs(title, url, body)
    print(f"  Generated {len(qa_pairs)} QA pairs")

    # Build JSONL records
    records = []
    for q, a in qa_pairs:
        records.append({
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": q.strip()},
                {"role": "assistant", "content": a.strip()}
            ],
            "source": url,
            "title": title
        })

    dataset_filename = f"{slug}_qa.jsonl"
    dataset_path_web = os.path.join(WEB_DS_DIR, dataset_filename)
    dataset_path_master = os.path.join(MASTER_DS_DIR, dataset_filename)

    for path in [dataset_path_web, dataset_path_master]:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"  Saved dataset: {dataset_filename}")

    entry = {
        "url": url,
        "title": title,
        "slug": slug,
        "status": "COMPLETED",
        "word_count": word_count,
        "qa_count": len(records),
        "text_file": text_file,
        "dataset_file": dataset_filename,
        "processed_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    _upsert_entry(reg, entry)
    save_registry(reg)
    return entry


def process_book_url(book_url: str, force: bool = False, delay: float = 1.0) -> List[dict]:
    """Fetch a book index/TOC page, discover all linked sections, and process them sequentially."""
    print(f"\n[Book Pipeline] Inspecting Table of Contents at: {book_url}")
    try:
        html = fetch_url(book_url)
    except Exception as e:
        print(f"[Book Pipeline] Error fetching book index: {e}")
        return []

    section_links = extract_toc_links(html, book_url)
    if not section_links:
        print(f"[Book Pipeline] No sub-sections found in TOC. Processing as single page...")
        return [process_url(book_url, force=force)]

    print(f"[Book Pipeline] Found {len(section_links)} section(s) in Table of Contents:")
    for idx, link in enumerate(section_links, 1):
        print(f"   {idx:02d}. {link}")

    results = []
    for link in section_links:
        res = process_url(link, force=force)
        results.append(res)
        time.sleep(delay)

    return results



def _upsert_entry(reg: dict, entry: dict):
    pages = reg.setdefault("pages", [])
    for i, p in enumerate(pages):
        if p["url"] == entry["url"]:
            pages[i] = entry
            return
    pages.append(entry)


def rebuild_master_splits():
    """Rebuild train/val splits from all datasets."""
    merge_script = os.path.join(ROOT_DIR, "merge_and_split_dataset.py")
    export_script = os.path.join(ROOT_DIR, "export_formats.py")
    splits_dir = os.path.join(ROOT_DIR, "datasets", "splits")
    if os.path.exists(merge_script):
        os.system(f'python "{merge_script}" --val-ratio 0.1 --output-dir "{splits_dir}"')
    if os.path.exists(export_script):
        os.system(f'python "{export_script}" --all-splits -f sharegpt')


# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════

def cmd_list():
    reg = load_registry()
    pages = reg.get("pages", [])
    if not pages:
        print("No web pages registered yet.")
        return
    print(f"\n{'#':<5} {'Status':<12} {'QA':<6} {'Title':<40} URL")
    print("-" * 100)
    for i, p in enumerate(pages, 1):
        status = p.get("status", "UNKNOWN")
        qa = p.get("qa_count", 0)
        title = p.get("title", "")[:38]
        url = p.get("url", "")[:55]
        print(f"{i:<5} {status:<12} {qa:<6} {title:<40} {url}")
    total_qa = sum(p.get("qa_count", 0) for p in pages)
    completed = sum(1 for p in pages if p.get("status") == "COMPLETED")
    print(f"\nTotal: {len(pages)} pages | {completed} completed | {total_qa} QA pairs")


def cmd_status():
    reg = load_registry()
    pages = reg.get("pages", [])
    completed = [p for p in pages if p.get("status") == "COMPLETED"]
    pending = [p for p in pages if p.get("status") == "PENDING"]
    errors = [p for p in pages if p.get("status") == "ERROR"]
    total_qa = sum(p.get("qa_count", 0) for p in completed)
    total_words = sum(p.get("word_count", 0) for p in completed)
    print(f"\n=== Web Page Pipeline Status ===")
    print(f"  Registered: {len(pages)}")
    print(f"  Completed:  {len(completed)}")
    print(f"  Pending:    {len(pending)}")
    print(f"  Errors:     {len(errors)}")
    print(f"  Total QA:   {total_qa}")
    print(f"  Total words processed: {total_words:,}")


def cmd_check(url: str):
    reg = load_registry()
    entry = find_page_entry(reg, url)
    if not entry:
        print(f"NOT FOUND: {url}")
    else:
        print(f"Status: {entry.get('status')}")
        print(f"Title:  {entry.get('title')}")
        print(f"QA pairs: {entry.get('qa_count', 0)}")
        print(f"Dataset: {entry.get('dataset_file')}")


def main():
    parser = argparse.ArgumentParser(
        description="Web Page → Dhamma Training Data Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("--add", nargs="+", metavar="URL",
                        help="Add and process one or more individual URLs")
    parser.add_argument("--book", nargs="+", metavar="BOOK_URL",
                        help="Process complete book(s) by extracting all sections from Table of Contents")
    parser.add_argument("--file", metavar="FILE",
                        help="Process URLs from a text file (one per line)")
    parser.add_argument("--reprocess", metavar="URL",
                        help="Re-fetch and regenerate QA for a specific URL")
    parser.add_argument("--list", action="store_true", help="List all registered pages")
    parser.add_argument("--status", action="store_true", help="Show summary statistics")
    parser.add_argument("--check", metavar="URL", help="Check if a URL has been processed")
    parser.add_argument("--no-rebuild", action="store_true",
                        help="Skip rebuilding master splits after processing")
    args = parser.parse_args()

    if args.list:
        cmd_list()
        return
    if args.status:
        cmd_status()
        return
    if args.check:
        cmd_check(args.check)
        return
    if args.reprocess:
        process_url(args.reprocess, force=True)
        if not args.no_rebuild:
            print("\nRebuilding master splits...")
            rebuild_master_splits()
        return

    any_processed = False
    total_book_qa = 0
    total_book_sections = 0

    if args.book:
        for b_url in args.book:
            results = process_book_url(b_url)
            comp = [r for r in results if r and r.get("status") == "COMPLETED"]
            total_book_sections += len(comp)
            total_book_qa += sum(r.get("qa_count", 0) for r in comp)
        print(f"\n{'='*60}")
        print(f"Book processing complete: {total_book_sections} substantive sections converted")
        print(f"Total new book QA pairs: {total_book_qa}")
        if total_book_sections > 0:
            any_processed = True

    urls = []
    if args.add:
        urls.extend(args.add)
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    urls.append(line)

    if not urls and not args.book:
        parser.print_help()
        return

    if urls:
        print(f"\nProcessing {len(urls)} URL(s)...")
        results = []
        for url in urls:
            entry = process_url(url)
            results.append(entry)
            time.sleep(1.0)  # polite delay between requests

        completed = [r for r in results if r and r.get("status") == "COMPLETED"]
        total_qa = sum(r.get("qa_count", 0) for r in completed)
        print(f"\n{'='*60}")
        print(f"URL processing complete: {len(completed)}/{len(urls)} pages converted")
        print(f"New QA pairs: {total_qa}")
        if completed:
            any_processed = True

    if not args.no_rebuild and any_processed:
        print("\nRebuilding master splits...")
        rebuild_master_splits()
    print("\nAll done.")


if __name__ == "__main__":
    main()


