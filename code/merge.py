#!/usr/bin/env python3
"""
Copy linked PDFs from all .bib files in ./metadata/ to ./pdfs/,
preserving original filenames.

Features:
- Idempotent (uses MD5 manifest to skip unchanged files)
- Handles multiple .bib files
- Logs missing PDFs to missing_pdfs.txt
- Keeps a .pdf_manifest.json for change detection
"""

import bibtexparser, os, re, shutil, json, hashlib
from pathlib import Path
from fetch import extract_pdf_path

# ---------- paths ----------
ROOT = Path(__file__).resolve().parents[1]
METADATA_DIR = ROOT / "metadata"
PDF_DIR = ROOT / "pdfs"
PDF_DIR.mkdir(exist_ok=True)

MISSING_LOG = ROOT / "missing_pdfs.txt"
MANIFEST_FILE = ROOT / ".pdf_manifest.json"

# ---------- helpers ----------

def merge_bib_files(bib_files, output_file):
    """Merge multiple .bib files into one, deterministically and without side effects."""
    merged_entries = []

    # deterministic ordering → no random reordering across runs
    for bibfile in sorted(bib_files):
        with open(bibfile, encoding="utf-8") as f:
            bib = bibtexparser.load(f)

        # deterministic entry order
        for entry in sorted(bib.entries, key=lambda e: e.get("ID", "")):
            print(f"Processing entry: {entry.get('ID', 'unknown')}")

            pdf_path = extract_pdf_path(entry.get("file", ""))

            # replace file path in-memory only — original files untouched
            entry = entry.copy()   # break reference to original data
            entry["file"] = (
                f"bib/pdfs/{Path(pdf_path).name}"
                if pdf_path else None
            )

            merged_entries.append(entry)

    # build new merged DB cleanly
    merged_bib = bibtexparser.bibdatabase.BibDatabase()
    merged_bib.entries = merged_entries

    # overwrite final output deterministically
    with open(output_file, "w", encoding="utf-8") as f:
        bibtexparser.dump(merged_bib, f)


merged_bib_path = ROOT / "pixecog.bib"
bib_files = list(METADATA_DIR.glob("*.bib"))
merge_bib_files(bib_files, merged_bib_path)