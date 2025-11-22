#!/usr/bin/env python
"""
Interactive CLI "chatbot" over the Chroma index.

For now this is *retrieval only* (no LLM): you type a question,
it returns the top-k chunks as markdown with clickable links.

Usage (from project root):

  python bib/rag/chatbot.py

Then type queries at the prompt. Type 'exit', 'quit' or Ctrl-D to leave.
"""

import sys
from pathlib import Path

import yaml
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings


HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[1]          # adjust if you move this under derivatives/
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


def format_result_markdown(query: str, docs):
    """
    Return a markdown string showing the query and retrieved chunks,
    with clickable links to source files (relative paths).
    """
    lines = []
    lines.append(f"## Query\n\n`{query}`\n")
    lines.append("## Results\n")

    if not docs:
        lines.append("_No results found._")
        return "\n".join(lines)

    for i, doc in enumerate(docs, start=1):
        meta = doc.metadata or {}
        corpus = meta.get("corpus", "unknown")
        source_id = meta.get("source_id", "unknown")
        source_path = meta.get("source_path", "")

        # Make a markdown link to the file (relative to project root)
        if source_path:
            link = f"[`{source_path}`]({source_path})"
        else:
            link = "_(no path)_"

        snippet = doc.page_content.strip().replace("\n", " ")
        if len(snippet) > 400:
            snippet = snippet[:400] + "..."

        lines.append(f"### {i}. `{source_id}` (_{corpus}_)")
        lines.append(f"- Source: {link}")
        lines.append("")
        lines.append(f"> {snippet}")
        lines.append("")

    return "\n".join(lines)


def main():
    db = get_vectorstore()
    retriever = db  # for now we'll just call similarity_search directly

    print("🔎 RAG chat (retrieval only). Type your question and press Enter.")
    print("Type 'exit' or 'quit' to leave.\n")

    try:
        while True:
            try:
                query = input(">>> ").strip()
            except EOFError:
                print("\n[exit]")
                break

            if not query:
                continue
            if query.lower() in {"exit", "quit"}:
                print("[exit]")
                break

            docs = retriever.similarity_search(query, k=4)
            md = format_result_markdown(query, docs)
            print()
            print(md)
            print("\n" + "-" * 60 + "\n")

    except KeyboardInterrupt:
        print("\n[exit]")


if __name__ == "__main__":
    main()
