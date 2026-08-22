import argparse
import json
import os
import re
import shutil
import sys
from typing import Dict, List, Optional

try:
    import pypdf
except ImportError:
    pypdf = None


def clean_pdf_text(text: str) -> str:
    """Clean common PDF extraction artifacts."""
    # Fix hyphenated words broken across line breaks
    text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)
    # Normalize multiple line breaks to maximum two
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Remove stand-alone page numbers on lines
    text = re.sub(r"\n\s*\d+\s*\n", "\n\n", text)
    return text.strip()


def sanitize_filename(name: str) -> str:
    """Sanitize string to be safe for filenames."""
    s = re.sub(r'[\\/*?:"<>|]', "", name)
    s = re.sub(r"\s+", " ", s).strip()
    return s[:100] if s else "Untitled"


def extract_pdf_book(pdf_path: str, output_base_dir: str = "documents/extracted") -> Optional[str]:
    """
    Extract a Dhamma PDF book into metadata, chapter files, and full_book.txt.
    """
    if pypdf is None:
        print("[Error] 'pypdf' package is not installed. Please run: pip install pypdf")
        return None

    if not os.path.exists(pdf_path):
        print(f"[Error] PDF file not found: {pdf_path}")
        return None

    print(f"[1/3] Parsing PDF document: {os.path.basename(pdf_path)}...")

    # Copy to raw_pdfs if not already there
    raw_pdfs_dir = os.path.join(os.path.dirname(output_base_dir), "raw_pdfs")
    os.makedirs(raw_pdfs_dir, exist_ok=True)
    dest_pdf = os.path.join(raw_pdfs_dir, os.path.basename(pdf_path))
    if os.path.abspath(pdf_path) != os.path.abspath(dest_pdf):
        shutil.copy2(pdf_path, dest_pdf)

    reader = pypdf.PdfReader(pdf_path)
    total_pages = len(reader.pages)

    # Extract metadata
    meta = reader.metadata or {}
    title = meta.get("/Title")
    author = meta.get("/Author")

    if not title or str(title).strip() in ("", "Untitled"):
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        title = base_name.replace("_", " ").replace("-", " ").strip()

    if not author or str(author).strip() in ("", "Unknown"):
        author = "Thai Forest Tradition"

    title = str(title).strip()
    author = str(author).strip()

    folder_name = sanitize_filename(f"{title} - {author}")
    book_dir = os.path.join(output_base_dir, folder_name)
    os.makedirs(book_dir, exist_ok=True)

    print(f"[2/3] Extracting text across {total_pages} pages for '{title}'...")

    # Extract text per page
    pages_text = []
    full_text_parts = []
    for p_idx, page in enumerate(reader.pages):
        try:
            t = page.extract_text() or ""
            t_clean = clean_pdf_text(t)
            pages_text.append(t_clean)
            if t_clean:
                full_text_parts.append(t_clean)
        except Exception as e:
            print(f"[Warning] Failed to extract page {p_idx + 1}: {e}")
            pages_text.append("")

    full_book_text = "\n\n".join(full_text_parts)

    # Detect chapters from outline or headings
    chapters = []
    outline = []
    try:
        outline = reader.outline or []
    except Exception:
        outline = []

    # If outline is present and structured
    if outline and isinstance(outline, list):
        for item in outline:
            if isinstance(item, list):
                continue
            title = getattr(item, "title", None) or (item.get("/Title") if hasattr(item, "get") else None)
            if title:
                c_title = str(title).strip()
                try:
                    p_num = reader.get_destination_page_number(item)
                    chapters.append({"title": c_title, "page": p_num})
                except Exception:
                    continue

    # Fallback chapter segmentation if no outline (e.g. group into sections or detect "Chapter" headings)
    if not chapters:
        # Scan for chapter headings like "Chapter 1", "Chapter I", or clear section headers
        current_chapter_title = "Chapter 1"
        current_chapter_pages = []
        c_index = 1

        for p_idx, p_text in enumerate(pages_text):
            lines = p_text.split("\n")
            header_match = False
            for line in lines[:5]:
                if re.match(r"^(Chapter\s+\d+|[IVXLCDM]+\.|\bPart\s+\d+)\b", line.strip(), re.IGNORECASE):
                    if current_chapter_pages:
                        c_text = "\n\n".join(current_chapter_pages).strip()
                        c_file = f"chapter_{c_index:02d}_{sanitize_filename(current_chapter_title)}.txt"
                        c_path = os.path.join(book_dir, c_file)
                        with open(c_path, "w", encoding="utf-8") as f:
                            f.write(f"# {current_chapter_title}\n\n{c_text}\n")
                        chapters.append({
                            "chapter_index": c_index,
                            "title": current_chapter_title,
                            "word_count": len(c_text.split()),
                            "file": c_file
                        })
                        c_index += 1
                        current_chapter_pages = []
                    current_chapter_title = line.strip()
                    header_match = True
                    break
            current_chapter_pages.append(p_text)

        if current_chapter_pages:
            c_text = "\n\n".join(current_chapter_pages).strip()
            c_file = f"chapter_{c_index:02d}_{sanitize_filename(current_chapter_title)}.txt"
            c_path = os.path.join(book_dir, c_file)
            with open(c_path, "w", encoding="utf-8") as f:
                f.write(f"# {current_chapter_title}\n\n{c_text}\n")
            chapters.append({
                "chapter_index": c_index,
                "title": current_chapter_title,
                "word_count": len(c_text.split()),
                "file": c_file
            })
    else:
        # Build chapters from outline destinations
        for idx, c in enumerate(chapters):
            start_p = c["page"]
            end_p = chapters[idx + 1]["page"] if idx + 1 < len(chapters) else total_pages
            c_text = "\n\n".join(pages_text[start_p:end_p]).strip()
            c_file = f"chapter_{idx + 1:02d}_{sanitize_filename(c['title'])}.txt"
            c_path = os.path.join(book_dir, c_file)
            with open(c_path, "w", encoding="utf-8") as f:
                f.write(f"# {c['title']}\n\n{c_text}\n")
            c["chapter_index"] = idx + 1
            c["word_count"] = len(c_text.split())
            c["file"] = c_file

    # Save full book text
    full_path = os.path.join(book_dir, "full_book.txt")
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(full_book_text)

    total_words = len(full_book_text.split())

    # Save metadata.json
    metadata = {
        "title": title,
        "author": author,
        "language": "en",
        "total_pages": total_pages,
        "total_chapters": len(chapters),
        "total_words": total_words,
        "chapters": chapters,
    }
    meta_path = os.path.join(book_dir, "metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"[3/3] PDF extraction completed successfully!")
    print(f"      Extracted folder: {book_dir}")
    print(f"      Total words: {total_words:,}")
    print(f"      Total chapters: {len(chapters)}")

    return book_dir


def main():
    parser = argparse.ArgumentParser(description="Extract Dhamma PDF books into chapters and text.")
    parser.add_argument("pdf_path", help="Path to the .pdf book file")
    parser.add_argument(
        "--output-dir",
        "-o",
        default="documents/extracted",
        help="Base directory for extracted output (default: 'documents/extracted')",
    )

    args = parser.parse_args()
    extract_pdf_book(args.pdf_path, args.output_dir)


if __name__ == "__main__":
    main()
