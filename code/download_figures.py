#!/usr/bin/env python
import sys
from pathlib import Path
import json
import requests
from bs4 import BeautifulSoup
from pybtex.database import parse_file

PROJECT = Path(__file__).resolve().parents[1]
BIB = PROJECT / "pixecog.bib"
bib_db = parse_file(str(BIB))

def get_entry(key):
    return bib_db.entries[key]

def get_doi(entry):
    return entry.fields.get("doi")

def main():
    if len(sys.argv) != 3:
        print("Usage: download_figures.py <citekey> <outdir>")
        sys.exit(1)

    citekey = sys.argv[1]
    outdir = Path(sys.argv[2])
    figs_dir = outdir / "figs"
    figs_dir.mkdir(parents=True, exist_ok=True)

    entry = get_entry(citekey)
    doi = get_doi(entry)
    if not doi:
        print(f"[online] no DOI for {citekey}")
        return  # success, but nothing downloaded

    headers = {"User-Agent": "pixecog-figures-bot/0.1 (personal research)"}
    try:
        resp = requests.get(f"https://doi.org/{doi}", headers=headers,
                            timeout=15, allow_redirects=True)
    except Exception as e:
        print(f"[online] DOI request failed: {e}")
        return

    if resp.status_code != 200:
        print(f"[online] HTTP {resp.status_code} for DOI {doi}")
        return

    final_url = resp.url
    soup = BeautifulSoup(resp.text, "html.parser")

    img_urls = []
    for fig in soup.find_all("figure"):
        for img in fig.find_all("img"):
            src = img.get("data-src") or img.get("src")
            if src:
                img_urls.append(requests.compat.urljoin(final_url, src))

    # crude extra selectors
    for selector in ['div.figures', 'div.figure', 'div.fig', 'li.fig', 'li.figure']:
        for container in soup.select(selector):
            for img in container.find_all("img"):
                src = img.get("data-src") or img.get("src")
                if src:
                    img_urls.append(requests.compat.urljoin(final_url, src))

    # dedupe
    seen = set()
    img_urls = [u for u in img_urls if not (u in seen or seen.add(u))]

    downloaded = []
    for i, url in enumerate(img_urls, start=1):
        try:
            r = requests.get(url, headers=headers, timeout=15)
        except Exception as e:
            print(f"[online] download failed {url}: {e}")
            continue
        if r.status_code != 200:
            continue

        ext = ".png"
        for cand in (".png", ".jpg", ".jpeg", ".tif", ".gif"):
            if cand in url.lower():
                ext = cand
                break

        fname = figs_dir / f"figure_{i}{ext}"
        fname.write_bytes(r.content)
        downloaded.append({"url": url, "file": fname.name})
        print(f"[online] {url} -> {fname}")

    if downloaded:
        meta = {
            "source": "online",
            "doi": doi,
            "publisher_url": final_url,
            "figures": downloaded,
        }
        (outdir / "meta.json").write_text(json.dumps(meta, indent=2))
    else:
        print(f"[online] no usable figures found for {citekey}")

if __name__ == "__main__":
    main()
