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

# ---------- paths ----------
ROOT = Path(__file__).resolve().parents[1]
METADATA_DIR = ROOT / "metadata"
PDF_DIR = ROOT / "pdfs"
PDF_DIR.mkdir(exist_ok=True)

MISSING_LOG = ROOT / "missing_pdfs.txt"
MANIFEST_FILE = ROOT / ".pdf_manifest.json"
PDF_FETCHED_LOG = PDF_DIR / "fetched_pdfs.txt"

# ---------- helpers ----------

def clean_text(s: str) -> str:
    """Remove braces and LaTeX markup, just to normalize."""
    if not s:
        return ""
    s = re.sub(r"[{}]", "", s)
    s = re.sub(r"\\[A-Za-z]+(\s*\{[^}]*\})?", "", s)
    s = re.sub(r"[^0-9A-Za-z _\-\.]+", "", s)
    return " ".join(s.split()).strip()

def extract_pdf_path(file_field: str) -> str | None:
    """Return the path to a .pdf file from a Better BibTeX file field."""
    if not file_field:
        return None

    # Better BibTeX often separates multiple files with ';'
    parts = [p.strip() for p in file_field.split(";")]
    for p in parts:
        if p.lower().endswith(".pdf"):
            return p

    # fallback
    if file_field.lower().endswith(".pdf"):
        return file_field.strip()

    return None


def md5sum(path: Path) -> str:
    """Compute MD5 checksum for file contents."""
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
	# ---------- load manifest ----------
	manifest = {}
	if MANIFEST_FILE.exists():
		try:
			manifest = json.loads(MANIFEST_FILE.read_text())
		except json.JSONDecodeError:
			manifest = {}

	# reset missing log
	if MISSING_LOG.exists():
		MISSING_LOG.unlink()

	if PDF_FETCHED_LOG.exists():
		PDF_FETCHED_LOG.unlink()
		PDF_FETCHED_LOG.touch()

	# ---------- main ----------
	for bibfile in sorted(METADATA_DIR.glob("*.bib")):
		print(f"📘 Processing {bibfile.name}...")
		with open(bibfile, encoding="utf-8") as f:
			bib = bibtexparser.load(f)

		for entry in bib.entries:
			key = entry.get("ID") or entry.get("key") or "unknown_key"
			file_field = entry.get("file")

			# no file field
			if not file_field:
				print(f"  ❌ No file field for: {key}")
				with open(MISSING_LOG, "a", encoding="utf-8") as f:
					f.write(f"No file field: {key}\n")
				continue

			pdf_path = extract_pdf_path(file_field)
			if not pdf_path or not os.path.exists(pdf_path):
				print(f"  ❌ No PDF found for: {key}")
				with open(MISSING_LOG, "a", encoding="utf-8") as f:
					f.write(f"No PDF: {key}\t{pdf_path or 'N/A'}\n")
				continue

			source = Path(pdf_path)
			target = PDF_DIR / source.name

			src_hash = md5sum(source)

			# idempotent copy
			if target.exists():
				prev_hash = manifest.get(target.name)
				if prev_hash == src_hash:
					print(f"  ↩︎ Skipping (unchanged): {target.name}")
					continue
				else:
					print(f"  ⚠️ Overwriting changed file: {target.name}")
					shutil.copy(source, target)
			else:
				shutil.copy(source, target)
				print(f"  ✅ Copied: {target.name}")
				with open(PDF_FETCHED_LOG, "a", encoding="utf-8") as f:
					f.write(f"{target.name}\n")
			manifest[target.name] = src_hash


	# ---------- save manifest ----------
	MANIFEST_FILE.write_text(json.dumps(manifest, indent=2))
	print("\n✨ Done. PDFs copied (names preserved).")
	print(f"🧾 Manifest saved to {MANIFEST_FILE}")
	print(f"🪶 Missing file list written to {MISSING_LOG}")

if __name__ == "__main__":
	main()