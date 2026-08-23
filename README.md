# Dhamma Training Pipeline (YouTube & EPUB to Chat SFT Datasets)

An automated pipeline for converting Dhamma talks (YouTube videos) and Dhamma books (EPUB documents) into high-quality instruction-tuning and Chat SFT datasets for LLMs.

---

## Folder Structure & What to Push to GitHub

When committing this repository to GitHub, the root directory of your repository should be `dhamma/` (or all files directly inside your repo root).

```
dhamma/
├── datasets/                 # [COMMIT] Generated Chat SFT JSONL training pairs (*.jsonl)
│   ├── A_Dhammapada_for_Contemplation_qa.jsonl
│   ├── Alert_to_the_Needs_of_the_Journey_qa.jsonl
│   ├── Cittaviveka_qa.jsonl
│   ├── Daughters_and_Sons_qa.jsonl
│   ├── Dhammapada_Reflections_Vol1_qa.jsonl
│   ├── Dhammapada_Reflections_Vol2_qa.jsonl
│   ├── Dhammapada_Reflections_Vol3_qa.jsonl
│   ├── Direct_Realization_qa.jsonl
│   ├── Fear_Buddhadasa_Bhikkhu_qa.jsonl
│   ├── Gratitude_qa.jsonl
│   ├── In_Any_Given_Moment_qa.jsonl
│   ├── In_Simple_Terms_Similes_qa.jsonl
│   ├── Intuitive_Awareness_qa.jsonl
│   ├── Its_Like_This_108_Dhamma_Similes_qa.jsonl
│   ├── Knowing the mood of the mind_qa.jsonl
│   ├── Luang Por Viradhammo - Reflections on the Dhamma, Seeking Happiness_qa.jsonl
│   ├── Mindfulness_Precepts_and_Crashing_in_the_Same_Car_qa.jsonl
│   ├── Mindfulness_The_Path_to_the_Deathless_qa.jsonl
│   ├── Now_is_the_Knowing_qa.jsonl
│   ├── On_Love_qa.jsonl
│   ├── Peace_is_a_Simple_Step_qa.jsonl
│   ├── Sanity_in_the_Midst_of_Uncertainty_qa.jsonl
│   ├── Seen_in_Their_True_Light_qa.jsonl
│   ├── Servant_of_Reality_qa.jsonl
│   ├── Sitting_in_the_Buddhas_Waiting_Room_qa.jsonl
│   ├── Stillness_Flowing_qa.jsonl
│   ├── Teachings_From_the_Forest_qa.jsonl
│   ├── The_Collected_Teachings_of_Ajahn_Chah_qa.jsonl
│   ├── The_Contemplatives_Companion_qa.jsonl
│   ├── The_Contemplatives_Craft_qa.jsonl
│   ├── The_Four_Noble_Truths_qa.jsonl
│   ├── The_Real_Practice_qa.jsonl
│   ├── The_Stillness_of_Being_qa.jsonl
│   ├── The_Way_It_Is_qa.jsonl
│   ├── The_Wheel_of_Truth_qa.jsonl
│   ├── True_But_Not_Right_qa.jsonl
│   ├── We_Are_All_Translators_qa.jsonl
│   ├── Without_and_Within_qa.jsonl
│   ├── splits/               # [COMMIT] Merged master + train/val splits
│   │   ├── master_dhamma_qa.jsonl
│   │   ├── train.jsonl
│   │   └── val.jsonl
│   └── exports/              # [COMMIT] Format-converted exports (ShareGPT, Alpaca)
│       ├── master_dhamma_qa_sharegpt.json
│       ├── train_sharegpt.json
│       └── val_sharegpt.json
├── documents/
│   ├── raw_epubs/            # [OPTIONAL / .gitignore] Source .epub files
│   ├── raw_pdfs/             # [OPTIONAL / .gitignore] Source .pdf files
│   └── extracted/            # [COMMIT] Extracted chapter texts and metadata.json
│       ├── A Dhammapada for Contemplation - Ajahn Munindo/
│       ├── Aj Jaya The Real Practice (WPN)/
│       ├── Ajahn Sumedho Volume 1 - Peace is a Simple Step - Ajahn Sumedho/
│       ├── Ajahn Sumedho Volume 3 - Direct Realization - Ajahn Sumedho/
│       ├── Ajahn Sumedho Volume 5 - The Wheel of Truth - Ajahn Sumedho/
│       ├── Alert to the Needs of the Journey - Ajahn Munindo/
│       ├── Cittaviveka - Ajahn Sumedho/
│       ├── Daughters & Sons - Ajahn Jayasaro/
│       ├── Dhammapada Reflections Volume 2 - Ajahn Munindo/
│       ├── Dhammapada Reflections Volume One - Ajahn Munindo/
│       ├── Dhammapada Reflections Volume Three - Ajahn Munindo/
│       ├── Fear - Buddhadasa Bhikkhu/
│       ├── Gratitude Ajahn Sumedho - Thai Forest Tradition/
│       ├── In Any Given Moment - Ajahn Munindo/
│       ├── In Simple Terms 108 Dhamma Similes - Venerable Ajahn Chah/
│       ├── Intuitive Awareness - Ajahn Sumedho/
│       ├── It's Like This 108 Dhamma Similes - Venerable Ajahn Chah/
│       ├── Mindfulness The Path to the Deathless - Ajahn Sumedho/
│       ├── Mindfulness, Precepts and Crashing in the Same Car - Ajahn Jayasaro/
│       ├── Now is the Knowing - Ajahn Sumedho/
│       ├── On Love - Ajahn Jayasaro/
│       ├── Sanity in the Midst of Uncertainty - Ajahn Munindo/
│       ├── Seen in Their True Light Spread by Ajahn Jayasaro - Thai Forest Tradition/
│       ├── Servant of Reality - Ajahn Munindo/
│       ├── Sitting in the Buddha's Waiting Room - Ajahn Munindo/
│       ├── Still Flowing Water - Ajahn Chah/
│       ├── Stillness Flowing - Ajahn Jayasaro/
│       ├── Teachings From the Forest/
│       ├── The Collected Teachings of Ajahn Chah - Single Volume - Ajahn Chah/
│       ├── The contemplative's companion - Ajahn Viradhammo/
│       ├── The Contemplative's Craft - Ajahn Viradhammo/
│       ├── The Four Noble Truths - Ajahn Sumedho/
│       ├── The Stillness of Being - Viradhammo Bhikkhu/
│       ├── The Way it is.indd - Thai Forest Tradition/
│       ├── true but not right - Thai Forest Tradition/
│       ├── We Are All Translators - Ajahn Munindo/
│       └── without and within - Ajahn Jayasaro/
├── transcripts/              # [COMMIT] Extracted talk transcripts (*.txt)
│   ├── Knowing the mood of the mind.txt
│   └── Luang Por Viradhammo - Reflections on the Dhamma, Seeking Happiness.txt
├── build_dataset.py          # [COMMIT] Standardized Chat SFT JSONL builder
├── merge_and_split_dataset.py# [COMMIT] Dataset merger, deduplicator & train/val splitter
├── export_formats.py         # [COMMIT] Format converter (ShareGPT, Alpaca)
├── corpus_summary.py         # [COMMIT] Corpus inventory & quality/coverage health audit
├── eval_prompts.py           # [COMMIT] Post-training evaluation benchmark suite
├── extract_epub.py           # [COMMIT] EPUB metadata and chapter extractor
├── extract_pdf.py            # [COMMIT] PDF metadata and chapter extractor
├── extract_transcript.py     # [COMMIT] YouTube transcript extractor & cleaner
├── verify_dataset.py         # [COMMIT] JSONL schema and content validator
├── requirements.txt          # [COMMIT] Python dependencies
├── RULES.md                  # [COMMIT] Persona guidelines, Pāli terminology, and SOP
├── README.md                 # [COMMIT] Project documentation
└── .gitignore                # [COMMIT] Git ignore rules
```

---

## Quickstart

### 1. Install Requirements
```bash
pip install -r requirements.txt
```

### 2. Process an EPUB Book
Place your `.epub` file into `documents/raw_epubs/` (or pass its path) and run:
```bash
python extract_epub.py "documents/raw_epubs/my_book.epub"
```
The script will:
1. Save the file into `documents/raw_epubs/`.
2. Extract Title, Author, Language, and Chapter List into `metadata.json`.
3. Extract each chapter as a clean markdown/text file (`chapter_01_Title.txt`, etc.).
4. Generate `full_book.txt` containing the entire text.
5. Save everything inside `documents/extracted/<Book Title - Author>/`.

### 3. Process a PDF Book
Place your `.pdf` file into `documents/raw_pdfs/` (or pass its path) and run:
```bash
python extract_pdf.py "documents/raw_pdfs/my_book.pdf"
```

### 4. Process a YouTube Video
```bash
python extract_transcript.py "https://www.youtube.com/watch?v=VIDEO_ID"
```
Saves cleaned transcript to `transcripts/<Video_Title>.txt`.

### 5. Generate Training QA Pairs with Antigravity IDE
In Antigravity chat, provide the YouTube URL, EPUB, or PDF path, or ask:
> *"Process book in `documents/extracted/<Book_Name>/` into training QA pairs."*

Antigravity will:
1. Follow [RULES.md](file:///c:/training-dhamma/dhamma/RULES.md).
2. Generate comprehensive Chat SFT pairs in Thai Forest Tradition teacher persona.
3. Save output to `datasets/<Book_Name>_qa.jsonl`.
4. Validate schema using `verify_dataset.py`.

### 6. Build and Verify Datasets Programmatically
You can compile raw QA pairs (JSON list of `[question, answer]` or `{"user": "...", "assistant": "..."}`) into a verified Chat SFT JSONL dataset:
```bash
python build_dataset.py --input raw_qa.json --output datasets/my_dataset_qa.jsonl
```
Or import it directly in Python:
```python
from build_dataset import build_dataset

qa_pairs = [
    ("How do I practice with anger?", "When anger arises, notice the raw feeling in the body..."),
]
build_dataset(qa_pairs, "datasets/my_dataset_qa.jsonl")
```

### 7. Verify Dataset
```bash
python verify_dataset.py "datasets/<file_name>_qa.jsonl"
```

### 8. Inspect Corpus Inventory & Word Statistics
```bash
python corpus_summary.py
```

### 9. Merge and Create Train/Validation Splits
```bash
python merge_and_split_dataset.py --val-ratio 0.1 --output-dir datasets/splits
```

### 10. Export to Fine-Tuning Formats (ShareGPT / Alpaca)
```bash
python export_formats.py --input datasets/splits/train.jsonl --output datasets/splits/train_sharegpt.json --format sharegpt
```

### 11. Run Post-Training Evaluation Benchmarks
Inspect the standardized Dhamma evaluation prompts or export them for automated LLM testing:
```bash
# Print prompts to console
python eval_prompts.py

# Export benchmark suite to JSONL
python eval_prompts.py --export "eval/benchmark_prompts.jsonl" --format jsonl
```
