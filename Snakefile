from pathlib import Path
import re

from pybtex.database import parse_file
from code.figconfig import get_citekeys

PROJECT = Path(__file__).resolve().parent   # pixecog/bib
BIB = PROJECT / "pixecog.bib"
CONFIG_MD = PROJECT / "figures.md"

# !! Set this to where your jar actually lives:
PDFFIGURES_JAR = str(Path.home() / "pdffigures2.jar")

# ---------- Config-derived lists ----------

# 1) Which citekeys to process (from figures.md)
CITEKEYS = get_citekeys(CONFIG_MD)

# 2) Parse BibTeX so we can map citekey -> PDF path (via 'file' field)
bib_db = parse_file(str(BIB))

def pdf_for_key(key: str) -> Path:
    """
    Look up the 'file' field for a BibTeX entry and return it as a Path.
    Example file field: bib/pdfs/Kajikawa...pdf
    We resolve it relative to the project root (one level up from pixecog/bib).
    """
    entry = bib_db.entries[key]
    file_field = entry.fields.get("file")
    if not file_field:
        raise ValueError(f"No 'file' field in BibTeX entry {key}")

    # If you have Zotero-style 'file = {path:stuff:pdf}', you'd parse here.
    # Your example is just 'bib/pdfs/...', so this is enough:
    pdf_rel = Path(file_field)
    return PROJECT.parent / pdf_rel  # project root is one level up

rule all:
    input:
        "pixecog.bib",
        expand("figures/{key}/pdffigures2", key=CITEKEYS)
        # We treat the whole pdffigures2 output dir as a "directory" target
    shell:
        "echo 'All done!'"

rule fetch:
    input:
        "metadata"
    output:
        "fetched_pdfs.txt"
    shell:
        "python code/fetch.py"
    #LINK: ./code/fetch.py

rule merge:
    input:
        "fetched_pdfs"
    output:
        "pixecog.bib"
    shell:
        "python code/merge.py"

rule extract_figures:
    """
    Run pdffigures2 on the PDF associated with a given citekey.
    Produces:
      figures/{key}/pdffigures2/
        figs/...
        data_*.json
        stats.json
    """
    input:
        pdf=lambda wc: pdf_for_key(wc.key)
    output:
        directory("figures/{key}/pdffigures2")
    params:
        jar=PDFFIGURES_JAR,
        dpi=300
    shell:
        r"""
        mkdir -p {output}/figs

        java -jar {params.jar} \
          -i {params.dpi} \
          -m {output}/figs/ \
          -d {output}/data_ \
          -s {output}/stats.json \
          {input.pdf}
        """