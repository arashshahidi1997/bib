#!/usr/bin/env python
"""
Interactive CLI RAG chatbot over the Chroma index.

- Retrieval: Chroma + HuggingFaceEmbeddings
- Generation: Llama 3 via Ollama (local)

Usage (from project root):

  python bib/rag/chatbot.py

Type 'exit' or 'quit' or press Ctrl-D to leave.
"""

from pathlib import Path
import sys
import textwrap

import yaml
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage


HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[1]          # adjust if needed
CONFIG_PATH = HERE / "index_config.yaml"
CHROMA_DIR = HERE / "chroma_db"


# ---------- Config & stores ----------

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


def get_llm():
    """
    Returns a chat model. Here we use Llama 3 via Ollama.
    Make sure you have `ollama` running and `ollama pull llama3`.
    """
    return ChatOllama(model="llama3")


# ---------- Formatting helpers ----------

def build_context_block(docs):
    """
    Build a text block to feed into the LLM, summarizing the retrieved docs.
    """
    parts = []
    for i, doc in enumerate(docs, start=1):
        meta = doc.metadata or {}
        corpus = meta.get("corpus", "unknown")
        source_id = meta.get("source_id", f"doc_{i}")
        source_path = meta.get("source_path", "")

        header = f"[Source {i}] id={source_id}, corpus={corpus}, path={source_path}"
        parts.append(header)
        parts.append(doc.page_content)
        parts.append("")  # blank line
    return "\n".join(parts)


def format_sources_markdown(docs):
    """
    Format a "Sources" section in markdown listing the retrieved docs.
    """
    lines = []
    lines.append("## Sources\n")
    if not docs:
        lines.append("_No sources retrieved._")
        return "\n".join(lines)

    for i, doc in enumerate(docs, start=1):
        meta = doc.metadata or {}
        corpus = meta.get("corpus", "unknown")
        source_id = meta.get("source_id", f"doc_{i}")
        source_path = meta.get("source_path", "")

        if source_path:
            link = f"[`{source_path}`]({source_path})"
        else:
            link = "`<unknown>`"

        snippet = doc.page_content.strip().replace("\n", " ")
        if len(snippet) > 160:
            snippet = snippet[:160] + "..."

        lines.append(f"### {i}. `{source_id}` (_{corpus}_)")
        lines.append(f"- Source: {link}")
        lines.append(f"- Snippet: {snippet}")
        lines.append("")
    return "\n".join(lines)


# ---------- Main chat loop ----------

def main():
    db = get_vectorstore()
    llm = get_llm()

    print("🤖 RAG chat (Llama 3 + Chroma).")
    print("Ask a question and press Enter.")
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

            # 1) Retrieve
            docs = db.similarity_search(query, k=4)

            # 2) Build context for the LLM
            context = build_context_block(docs)

            # 3) Build prompt messages
            system_msg = SystemMessage(content=textwrap.dedent("""
                You are a helpful research assistant for the 'pixecog' project.
                You answer strictly based on the provided sources.
                If the sources do not contain enough information, say so clearly.
                Use concise but clear markdown in your answer.
            """).strip())

            user_content = textwrap.dedent(f"""
                Question:
                {query}

                Context from retrieved sources:
                {context}

                Instructions:
                - Answer the question using only the information in the context.
                - If the answer is uncertain or incomplete, say so.
                - Do NOT invent sources or details that are not present.
                - Write the answer in markdown.
            """).strip()

            user_msg = HumanMessage(content=user_content)

            # 4) Call the LLM
            print("\n[LLM] Thinking...\n")
            response = llm.invoke([system_msg, user_msg])

            # 5) Print answer + sources
            print("## Answer\n")
            print(response.content.strip())
            print()
            print(format_sources_markdown(docs))
            print("\n" + "-" * 60 + "\n")

    except KeyboardInterrupt:
        print("\n[exit]")


if __name__ == "__main__":
    main()
