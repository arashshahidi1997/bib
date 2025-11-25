import re
from pathlib import Path
import yaml
from .repo_root import repo_abs

CONFIGFILE = repo_abs("config/config.yaml")

def load_config(configfile=CONFIGFILE):
    with configfile.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)
    
def get_citekeys(md_path: str | Path):
    """
    Extract all @citekeys from a markdown file.
    Returns a sorted list of unique keys (without the @).
    """
    md_path = Path(md_path)
    text = md_path.read_text(encoding="utf-8")
    keys = set(re.findall(r'@([\w:-]+)', text))
    return sorted(keys)

def get_bib_paths():
    """
    From config dict, get list of .bib file paths.
    project_bib: "neuropy.bib"
    extract_config: "extract_config.md"
    bib_src_dir: "src"
    pdf_dir: "pdfs"
    missing_log: "logs/missing_pdfs.txt"
    manifest_file: "logs/.pdf_manifest.json"
    pdf_fetched_log: "logs/fetched_pdfs.txt"
    """
    config = load_config()
    bib_paths = config['paths']
    for key in bib_paths:
        bib_paths[key] = repo_abs(bib_paths[key])
        # make parent dirs
        bib_paths[key].parent.mkdir(parents=True, exist_ok=True)
    return bib_paths