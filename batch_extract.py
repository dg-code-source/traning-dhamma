#!/usr/bin/env python3
"""
batch_extract.py — Batch Document Extractor for EPUB and PDF Books

Scans documents/raw_epubs/ and documents/raw_pdfs/ and extracts all un-extracted
books into documents/extracted/<Book Title - Author>/ with metadata.json and chapter texts.
"""

import os
import glob
import sys
from extract_epub import extract_epub, EBOOKLIB_AVAILABLE
from extract_pdf import extract_pdf_book

# Fix Windows console UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main():
    raw_epubs = sorted(glob.glob("documents/raw_epubs/*.epub"))
    raw_pdfs = sorted(glob.glob("documents/raw_pdfs/*.pdf"))
    extracted_base = "documents/extracted"
    os.makedirs(extracted_base, exist_ok=True)

    print(f"=== BATCH EXTRACTOR ===")
    print(f"Found {len(raw_epubs)} raw EPUBs and {len(raw_pdfs)} raw PDFs.\n")

    extracted_count = 0
    skipped_count = 0

    # 1. Process EPUBs
    print("--- Processing EPUBs ---")
    for epub_path in raw_epubs:
        fname = os.path.basename(epub_path)
        if fname.startswith("test_book"):
            continue
        try:
            res = extract_epub(epub_path)
            if res:
                extracted_count += 1
            else:
                skipped_count += 1
        except Exception as e:
            print(f"[Error] Failed to extract {fname}: {e}")

    # 2. Process PDFs
    print("\n--- Processing PDFs ---")
    for pdf_path in raw_pdfs:
        fname = os.path.basename(pdf_path)
        try:
            out_dir = extract_pdf_book(pdf_path, output_base_dir=extracted_base)
            if out_dir:
                extracted_count += 1
            else:
                skipped_count += 1
        except Exception as e:
            print(f"[Error] Failed to extract {fname}: {e}")

    print(f"\n==========================================")
    print(f"Batch Extraction Completed!")
    print(f"Total Processed / Extracted: {extracted_count}")
    print(f"Total Extracted Books in {extracted_base}: {len(os.listdir(extracted_base))}")
    print(f"==========================================\n")


if __name__ == "__main__":
    main()
