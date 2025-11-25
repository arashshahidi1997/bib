from pathlib import Path
import re

from pybtex.database import parse_file
from bib.load_config import get_citekeys, get_bib_paths
bib_paths = get_bib_paths()

def pdf_for_key(key: str) -> Path:
    """
    Look up the 'file' field for a BibTeX entry and return it as a Path.
    Example file field: bib/pdfs/Kajikawa...pdf
    We resolve it relative to the project root (one level up from pixecog/bib).
    """
    # Parse BibTeX so we can map citekey -> PDF path (via 'file' field)
    bib_db = parse_file(str(bib_paths['project_bib']))

    entry = bib_db.entries[key]
    file_field = entry.fields.get("file")
    if not file_field:
        raise ValueError(f"No 'file' field in BibTeX entry {key}")

    # If you have Zotero-style 'file = {path:stuff:pdf}', you'd parse here.
    # Your example is just 'bib/pdfs/...', so this is enough:
    pdf_rel = Path(file_field)
    # drop 'bib/' prefix if present
    if pdf_rel.parts[0] == "bib":
        pdf_rel = Path(*pdf_rel.parts[1:])

    return pdf_rel  # project root is one level up


# ---------- Config-derived lists ----------

# 1) Which citekeys to process (from figures.md)
CITEKEYS = get_citekeys(bib_paths['extract_config'])


rule all:
    input:
        bib_paths['project_bib'],
        expand("derivatives/figures/{key}/online", key=CITEKEYS),
        expand("derivatives/figures/{key}/pdffigures2", key=CITEKEYS),
        expand("derivatives/fulltext/{key}/online", key=CITEKEYS),
        expand("derivatives/fulltext/{key}/pdf", key=CITEKEYS)
        # expand("figures/{key}/pdffigures2", key=CITEKEYS)
        # We treat the whole pdffigures2 output dir as a "directory" target
    shell:
        "echo 'All done!'"

rule fetch:
    input:
        bib_paths['bib_src_dir']
    output:
        bib_paths['pdf_fetched_log']
    shell:
        "python -m bib.fetch"

rule merge:
    input:
        bib_paths['pdf_fetched_log']
    output:
        bib_paths['project_bib']
    shell:
        "python -m bib.merge"

rule extract_figures:
    input:
        pdf=lambda wc: pdf_for_key(wc.key)
    output:
        directory("derivatives/figures/{key}/pdffigures2")
    params:
        dpi=300
    shell:
        """
        mkdir -p {output}/figs

        pdffigures \
          -i {params.dpi} \
          -m {output}/figs/ \
          -d {output}/data_ \
          -s {output}/stats.json \
          '{input.pdf}'
        """

rule download_figures:
    output:
        out_dir = directory("derivatives/figures/{key}/online")
    log: "derivatives/figures/{key}/download.log"
    shell:
        "python -m bib.download_figures {wildcards.key} {output.out_dir} > {log} 2>&1"

rule download_fulltext:
    output:
        directory("derivatives/fulltext/{key}/online")
    shell:
        """
        mkdir -p {output}
        python -m bib.download_fulltext {wildcards.key} {output}
        """

rule extract_fulltext_pdf:
    output:
        directory("derivatives/fulltext/{key}/pdf")
    shell:
        """
        mkdir -p {output}
        python -m bib.pdf_fulltext {wildcards.key} {output}
        """
