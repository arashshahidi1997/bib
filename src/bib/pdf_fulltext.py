#!/usr/bin/env python
import sys
from pathlib import Path
from pybtex.database import parse_file
from pdfminer.high_level import extract_text
from .load_config import get_bib_paths
from .repo_root import repo_abs

bib_paths = get_bib_paths()
bib_db = parse_file(str(bib_paths['project_bib']))

def pdf_for_key(key):
    entry = bib_db.entries[key]
    file_field = entry.fields.get("file")
    if not file_field:
        raise RuntimeError(f"No file= field for {key}")
    pdf_rel = Path(file_field)
    if pdf_rel.parts[0] == "bib":
        pdf_rel = Path(*pdf_rel.parts[1:])
    return repo_abs(pdf_rel)

def main():
    key, outdir = sys.argv[1], Path(sys.argv[2])
    outdir.mkdir(parents=True, exist_ok=True)

    pdf_path = pdf_for_key(key)
    text = extract_text(str(pdf_path))

    txt_out = outdir / "full.txt"
    txt_out.write_text(text, encoding="utf-8")

if __name__ == "__main__":
    main()
