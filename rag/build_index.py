#!/usr/bin/env python
"""
Build a minimal Chroma index from:
  - bib/README.md
  - docs/README.md

Run from project root:
  python bib/rag/build_index.py
"""

import json
from pathlib import Path

import yaml
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document


HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[1]           # .../pixecog
CONFIG_PATH = HERE / "index_config.yaml"
CHROMA_DIR = HERE / "chroma_db"


def load_config():
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def make_embeddings(model_name: str):
    # Lightweight, CPU-friendly default. Later you can swap this for Llama3 embeddings.
    return HuggingFaceEmbeddings(model_name=model_name)


def build_docs(config):
    docs = []

    for src in config.get("sources", []):
        src_id = src["id"]
        corpus = src["corpus"]

        # Case 1: Single file
        if "path" in src:
            path = PROJECT_ROOT / src["path"]
            if not path.exists():
                print(f"[WARN] Skipping {src_id}: file not found {path}")
                continue

            text = path.read_text(encoding="utf-8")
            metadata = {
                "source_id": src_id,
                "corpus": corpus,
                "source_path": str(path.relative_to(PROJECT_ROOT)),
            }
            docs.append(Document(page_content=text, metadata=metadata))
            print(f"[INFO] Loaded {src_id} from {path}")

        # Case 2: Glob
        elif "glob" in src:
            pattern = src["glob"]
            for path in PROJECT_ROOT.glob(pattern):
                if path.is_file():
                    text = path.read_text(encoding="utf-8")
                    metadata = {
                        "source_id": src_id,
                        "corpus": corpus,
                        "source_path": str(path.relative_to(PROJECT_ROOT)),
                    }
                    docs.append(Document(page_content=text, metadata=metadata))
                    print(f"[INFO] Loaded {src_id}: {path}")

    return docs


def split_docs(docs, chunk_size: int, chunk_overlap: int):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    split_docs = splitter.split_documents(docs)
    print(f"[INFO] Split into {len(split_docs)} chunks")
    return split_docs


def main():
    config = load_config()
    embedding_model_name = config["embedding_model"]
    chunk_size = config["chunk_size_chars"]
    chunk_overlap = config["chunk_overlap_chars"]

    print("[INFO] Config:", json.dumps(config, indent=2))

    docs = build_docs(config)
    if not docs:
        print("[ERROR] No documents to index. Aborting.")
        return

    chunks = split_docs(docs, chunk_size, chunk_overlap)

    embeddings = make_embeddings(embedding_model_name)

    # Clear existing DB (if any) by recreating the directory
    if CHROMA_DIR.exists():
        print(f"[INFO] Removing existing Chroma directory at {CHROMA_DIR}")
        for p in CHROMA_DIR.glob("**/*"):
            if p.is_file():
                p.unlink()
        for p in sorted(CHROMA_DIR.glob("**/*"), reverse=True):
            if p.is_dir():
                p.rmdir()

    print(f"[INFO] Building Chroma index at {CHROMA_DIR}")
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(CHROMA_DIR),
    )
    print("[INFO] Index build complete.")


if __name__ == "__main__":
    main()
