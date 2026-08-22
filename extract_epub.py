import os
import re
import sys
import json
import shutil
import argparse
import warnings
from typing import List, Dict, Any

try:
    import ebooklib
    from ebooklib import epub
    from bs4 import BeautifulSoup
    EBOOKLIB_AVAILABLE = True
except ImportError:
    EBOOKLIB_AVAILABLE = False

# Suppress BeautifulSoup warnings about XML-as-HTML parsing (EPUBs are XHTML)
try:
    from bs4 import XMLParsedAsHTMLWarning
    warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
except ImportError:
    pass


def sanitize_filename(name: str) -> str:
    """Sanitize string to be a safe filesystem directory/file name."""
    clean = re.sub(r'[\\/*?:"<>|]', '', name)
    # Strip trailing dots and asterisks that are common in EPUB headings
    clean = clean.strip().rstrip('.*')
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean if clean else "untitled_book"


def extract_chapter_title(html_bytes_or_str: Any) -> str:
    """Extract the primary chapter title from HTML by finding the first heading tag.

    This is separate from clean_html_content to avoid the issue of
    concatenated headings when using get_text() for title extraction.
    """
    if isinstance(html_bytes_or_str, bytes):
        html_str = html_bytes_or_str.decode('utf-8', errors='ignore')
    else:
        html_str = str(html_bytes_or_str)

    try:
        from bs4 import BeautifulSoup
        try:
            soup = BeautifulSoup(html_str, 'lxml')
        except Exception:
            soup = BeautifulSoup(html_str, 'html.parser')

        # Look for the first heading tag (h1 > h2 > h3 > h4)
        for tag_name in ['h1', 'h2', 'h3', 'h4']:
            heading = soup.find(tag_name)
            if heading:
                title = heading.get_text(separator=' ', strip=True)
                # Clean up asterisks, excessive whitespace
                title = re.sub(r'[*]+', '', title).strip()
                if len(title) > 3:
                    return title[:120]  # Allow longer titles than before (was 60)

        # No heading found — try the first non-empty text line
        body = soup.find('body')
        if body:
            text = body.get_text(separator='\n', strip=True)
        else:
            text = soup.get_text(separator='\n', strip=True)

        for line in text.splitlines():
            line = line.strip()
            if len(line) > 3 and len(line.split()) <= 15:  # Short enough to be a title
                return line[:120]
    except Exception:
        pass

    return ""


def clean_html_content(html_bytes_or_str: Any) -> str:
    """Convert HTML/XHTML to clean, structured plain text.

    Handles EPUB XHTML content with proper heading separation and
    paragraph spacing.
    """
    if isinstance(html_bytes_or_str, bytes):
        html_str = html_bytes_or_str.decode('utf-8', errors='ignore')
    else:
        html_str = str(html_bytes_or_str)

    soup = None
    try:
        from bs4 import BeautifulSoup
        try:
            soup = BeautifulSoup(html_str, 'lxml')
        except Exception:
            soup = BeautifulSoup(html_str, 'html.parser')
    except Exception:
        pass

    if soup is not None:
        # Remove script and style elements
        for element in soup(["script", "style", "nav"]):
            element.decompose()

        # Insert newline markers BEFORE and AFTER each heading to guarantee
        # they become separate paragraphs and don't concatenate with adjacent text.
        for h in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            heading_text = h.get_text(separator=' ', strip=True)
            if heading_text:
                level = int(h.name[1])
                hashes = "#" * level
                h.replace_with(f"\n\n{hashes} {heading_text}\n\n")

        # Insert paragraph breaks after block elements
        for tag in soup.find_all(['p', 'div', 'blockquote', 'li']):
            tag.append('\n\n')

        text = soup.get_text()
    else:
        # Fallback regex strip
        text = re.sub(r'<[^>]+>', ' ', html_str)

    # Clean whitespace and reconstruct paragraphs
    lines = [line.strip() for line in text.splitlines()]
    clean_paragraphs = []
    current_para = []

    for line in lines:
        if line:
            current_para.append(line)
        elif current_para:
            clean_paragraphs.append(" ".join(current_para))
            current_para = []

    if current_para:
        clean_paragraphs.append(" ".join(current_para))

    return "\n\n".join(clean_paragraphs).strip()


def _extract_chapters_from_items(items, content_getter, name_getter):
    """Common chapter extraction logic shared by both parsers.

    Args:
        items: Iterable of document items.
        content_getter: Callable(item) -> bytes/str of HTML content.
        name_getter: Callable(item) -> str filename of the item.

    Returns:
        List of chapter dicts.
    """
    chapters = []
    chapter_num = 1

    for item in items:
        raw_content = content_getter(item)
        clean_text = clean_html_content(raw_content)

        # Skip very short documents (cover pages, blank pages, etc.)
        word_count = len(clean_text.split())
        if word_count < 50:
            continue

        # Extract title from the original HTML, not from cleaned text
        ch_title = extract_chapter_title(raw_content)
        if not ch_title or len(ch_title) <= 3:
            ch_title = f"Chapter {chapter_num}"

        chapters.append({
            "index": chapter_num,
            "title": ch_title,
            "file_name": name_getter(item),
            "text": clean_text,
            "word_count": word_count
        })
        chapter_num += 1

    return chapters


def parse_epub_with_ebooklib(epub_path: str) -> Dict[str, Any]:
    """Parse EPUB using ebooklib and BeautifulSoup."""
    book = epub.read_epub(epub_path)

    # Metadata extraction
    title_list = book.get_metadata('DC', 'title')
    title = title_list[0][0] if title_list else os.path.splitext(os.path.basename(epub_path))[0]

    author_list = book.get_metadata('DC', 'creator')
    author = author_list[0][0] if author_list else "Unknown Author"

    lang_list = book.get_metadata('DC', 'language')
    language = lang_list[0][0] if lang_list else "en"

    doc_items = [item for item in book.get_items() if item.get_type() == ebooklib.ITEM_DOCUMENT]
    chapters = _extract_chapters_from_items(
        doc_items,
        content_getter=lambda item: item.get_content(),
        name_getter=lambda item: item.get_name()
    )

    return {
        "title": title,
        "author": author,
        "language": language,
        "total_chapters": len(chapters),
        "chapters": chapters
    }


def parse_epub_fallback(epub_path: str) -> Dict[str, Any]:
    """Fallback standard-library EPUB parser using zipfile and xml.etree."""
    import zipfile
    import xml.etree.ElementTree as ET

    with zipfile.ZipFile(epub_path, 'r') as z:
        # Locate container.xml
        container_xml = z.read('META-INF/container.xml')
        root = ET.fromstring(container_xml)
        rootfile_path = root.find('.//{*}rootfile').attrib['full-path']

        # Read OPF file
        opf_data = z.read(rootfile_path)
        opf_root = ET.fromstring(opf_data)

        # Namespaces
        ns = {'dc': 'http://purl.org/dc/elements/1.1/', 'opf': 'http://www.idpf.org/2007/opf'}

        title_elem = opf_root.find('.//dc:title', ns)
        title = title_elem.text if title_elem is not None and title_elem.text else os.path.splitext(os.path.basename(epub_path))[0]

        author_elem = opf_root.find('.//dc:creator', ns)
        author = author_elem.text if author_elem is not None and author_elem.text else "Unknown Author"

        lang_elem = opf_root.find('.//dc:language', ns)
        language = lang_elem.text if lang_elem is not None and lang_elem.text else "en"

        manifest = {}
        for item in opf_root.findall('.//opf:item', ns):
            manifest[item.attrib['id']] = item.attrib['href']

        spine_items = []
        for itemref in opf_root.findall('.//opf:itemref', ns):
            idref = itemref.attrib['idref']
            if idref in manifest:
                spine_items.append(manifest[idref])

        opf_dir = os.path.dirname(rootfile_path)

        # Build list of (content_bytes, filename) tuples from spine
        doc_items = []
        for href in spine_items:
            full_item_path = os.path.normpath(os.path.join(opf_dir, href)).replace('\\', '/')
            if full_item_path in z.namelist():
                content = z.read(full_item_path)
                doc_items.append((content, href))

        chapters = _extract_chapters_from_items(
            doc_items,
            content_getter=lambda item: item[0],
            name_getter=lambda item: item[1]
        )

    return {
        "title": title,
        "author": author,
        "language": language,
        "total_chapters": len(chapters),
        "chapters": chapters
    }


def extract_epub(epub_source_path: str, documents_dir: str = None) -> Dict[str, Any]:
    """Extract EPUB metadata and chapters into structured documents folder."""
    if not os.path.exists(epub_source_path):
        raise FileNotFoundError(f"EPUB file not found: '{epub_source_path}'")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    docs_dir = documents_dir or os.path.join(script_dir, "documents")
    raw_epubs_dir = os.path.join(docs_dir, "raw_epubs")
    extracted_dir = os.path.join(docs_dir, "extracted")

    os.makedirs(raw_epubs_dir, exist_ok=True)
    os.makedirs(extracted_dir, exist_ok=True)

    # Copy to raw_epubs if not already located there
    target_raw_epub = os.path.join(raw_epubs_dir, os.path.basename(epub_source_path))
    if os.path.abspath(epub_source_path) != os.path.abspath(target_raw_epub):
        shutil.copy2(epub_source_path, target_raw_epub)

    print(f"[1/3] Parsing EPUB document: {os.path.basename(epub_source_path)}...")
    if EBOOKLIB_AVAILABLE:
        try:
            parsed = parse_epub_with_ebooklib(target_raw_epub)
        except Exception as e:
            print(f"[Warning] EbookLib parsing error: {e}. Falling back to standard parser.")
            parsed = parse_epub_fallback(target_raw_epub)
    else:
        parsed = parse_epub_fallback(target_raw_epub)

    safe_book_name = sanitize_filename(f"{parsed['title']} - {parsed['author']}" if parsed['author'] != "Unknown Author" else parsed['title'])
    book_extracted_dir = os.path.join(extracted_dir, safe_book_name)
    os.makedirs(book_extracted_dir, exist_ok=True)

    print(f"[2/3] Extracting {parsed['total_chapters']} chapters for: '{parsed['title']}' by {parsed['author']}...")

    full_book_text = []
    chapter_files_summary = []

    for ch in parsed["chapters"]:
        ch_filename = f"chapter_{ch['index']:02d}_{sanitize_filename(ch['title'])}.txt"
        ch_path = os.path.join(book_extracted_dir, ch_filename)

        with open(ch_path, "w", encoding="utf-8") as f:
            f.write(ch["text"])

        chapter_files_summary.append({
            "chapter_index": ch["index"],
            "title": ch["title"],
            "word_count": ch["word_count"],
            "file": ch_filename
        })

        full_book_text.append(f"=== {ch['title']} ===\n\n{ch['text']}")

    # Save full book text
    full_book_path = os.path.join(book_extracted_dir, "full_book.txt")
    with open(full_book_path, "w", encoding="utf-8") as f:
        f.write("\n\n\n".join(full_book_text))

    # Save metadata.json
    meta_path = os.path.join(book_extracted_dir, "metadata.json")
    meta_info = {
        "title": parsed["title"],
        "author": parsed["author"],
        "language": parsed["language"],
        "total_chapters": parsed["total_chapters"],
        "total_words": sum(ch["word_count"] for ch in parsed["chapters"]),
        "chapters": chapter_files_summary
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta_info, f, indent=2, ensure_ascii=False)

    print(f"[3/3] Extraction completed successfully!")
    print(f"      Extracted folder: {book_extracted_dir}")
    print(f"      Total words: {meta_info['total_words']:,}")
    print(f"      Total chapters: {meta_info['total_chapters']}")

    return {
        "book_dir": book_extracted_dir,
        "metadata": meta_info
    }


def main():
    parser = argparse.ArgumentParser(description="Extract EPUB books into structured Dhamma chapters and text.")
    parser.add_argument("epub_path", help="Path to .epub file")
    parser.add_argument("--output_dir", "-o", default=None, help="Target documents directory")
    args = parser.parse_args()

    extract_epub(args.epub_path, args.output_dir)


if __name__ == "__main__":
    main()
