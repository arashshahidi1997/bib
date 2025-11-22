#!/usr/bin/env python
"""
Minimal CLI to query the Chroma index built from README files.

Usage (from project root):

  python bib/rag/query_cli.py "what is this project about?"

"""

import sys
from pathlib import Path

import yaml
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings


HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[1]
CONFIG_PATH = HERE / "index_config.yaml"
CHROMA_DIR = HERE / "chroma_db"


def load_config():
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_vectorstore():
    config = load_config()
    embedding_model_name = config["embedding_model"]
    embeddings = HuggingFaceEmbeddings(model_name=embedding_model_name)

    if not CHROMA_DIR.exists():
        raise SystemExit(f"No Chroma DB found at {CHROMA_DIR}. Run build_index.py first.")

    db = Chroma(
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DIR),
    )
    return db


def main():
    if len(sys.argv) < 2:
        print("Usage: query_cli.py \"your question here\"")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    print(f"[QUERY] {query}\n")

    db = get_vectorstore()
    docs = db.similarity_search(query, k=4)

    for i, doc in enumerate(docs, start=1):
        meta = doc.metadata
        print(f"=== Result {i} ===")
        print(f"Corpus     : {meta.get('corpus')}")
        print(f"Source ID  : {meta.get('source_id')}")
        print(f"Source Path: {meta.get('source_path')}")
        print("--- Snippet ---")
        # Show the first 400 characters of the chunk
        snippet = doc.page_content.strip().replace("\n", " ")
        print(snippet[:400] + ("..." if len(snippet) > 400 else ""))
        print()


if __name__ == "__main__":
    main()
