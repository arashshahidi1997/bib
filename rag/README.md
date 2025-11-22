# RAG index for pixecog

This directory contains the retrieval-augmented generation (RAG) index
for the project. The index is built with:

- LangChain
- Chroma (local vector store)
- HuggingFace sentence-transformer embeddings (can be swapped for Llama 3)

For now, the index only contains:

- `bib/README.md`  (corpus = "docs", source = "bib")
- `docs/README.md` (corpus = "docs", source = "docs")

Use `build_index.py` to (re)build the index, and `query_cli.py` to run
simple similarity search over the stored chunks.
