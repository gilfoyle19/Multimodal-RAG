# Multimodal RAG

Prototype for grounded troubleshooting answers from locally loaded technical manuals.

## V1 Process Flow

```mermaid
flowchart TD
    PDFs["Local PDFs in database/"] --> Ingest["POST /ingest"]
    Sidecars[Optional metadata sidecars] --> Ingest
    Ingest --> Extract[Extract text, tables, figures, previews]
    Extract --> SQLite[(SQLite metadata + FTS5)]
    Extract --> Artifacts[(Local data/ artifacts)]
    Extract --> Captions[OpenAI figure captions]
    Captions --> Cache[(OpenAI cache)]
    Captions --> SQLite
    SQLite --> FTS[Keyword retrieval]
    SQLite --> Embed[OpenAI embeddings]
    Embed --> Chroma[(ChromaDB vectors)]

    User[Technician question] --> Ask["POST /ask"]
    Ask --> Decompose[Contract-validated query decomposition]
    Decompose --> FTS
    Decompose --> Chroma
    FTS --> RRF[Reciprocal Rank Fusion]
    Chroma --> RRF
    RRF --> Rerank[Local reranker]
    Rerank --> Verify[OpenAI evidence verification]
    Verify --> Decision{Verified evidence?}
    Decision -->|None| NotFound[Deterministic not_found response]
    Decision -->|Some / all| Generate[Structured answer generation]
    Generate --> Answer[Grounded or partial answer with citations]
    SQLite --> Sources["GET /sources/{source_id}"]
    Artifacts --> Sources
    Answer --> Sources
    Ask --> Trace[(Ask trace)]
    Trace --> Evaluate["POST /evaluate"]
    Answer --> Evaluate
```

1. Place public digital PDFs in `database/`, optionally with matching metadata sidecars.
2. Run ingestion to extract citeable source elements, create previews, and index searchable chunks.
3. Store canonical metadata in SQLite, keyword search in SQLite FTS5, vectors in ChromaDB, and runtime artifacts under `data/`.
4. Answer questions through `/ask` using decomposition, hybrid retrieval, RRF, local reranking, hosted evidence verification, and structured answer generation from verified evidence only.
5. Return `grounded`, `partial`, or deterministic `not_found` responses with citations, source previews, confidence metadata, and ask traces.
6. Use `/retrieve`, `/sources/{source_id}`, and `/evaluate` to inspect retrieval, evidence, previews, and rubric scoring independently.

## Python Environment

```powershell
uv sync
uv run pytest
uv run ruff check .
uv run mypy .
```
