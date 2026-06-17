# V1 Prototype Design

## Goal

Build an end-to-end web prototype for field technicians troubleshooting from a small set of loaded technical PDFs. The prototype must prioritize deterministic, well-cited, manual-grounded answers over conversational breadth.

## Scope

In scope:

- Digital PDF ingestion from `database/`
- Optional per-document metadata sidecars
- Text extraction with page and section context
- Table extraction with whole-table preview and row-level retrieval helpers
- Figure extraction with previews and generated technical captions
- SQLite metadata store and SQLite FTS keyword search
- ChromaDB persistent vector search
- OpenAI embeddings
- Hybrid retrieval with Reciprocal Rank Fusion
- Local reranking with a small reranker model
- OpenAI evidence verification on the top candidates only
- OpenAI structured answer generation from verified evidence only
- Strict `grounded`, `partial`, and `not_found` behavior
- Source citations and source previews
- Manual evaluation set and scoring endpoint
- FastAPI backend and simple React/Vite frontend

Out of scope:

- Scanned PDF support and full-page OCR
- Asset-specific access control
- Multi-tenant users
- Work-order, CMMS, or ERP integrations
- Automatic manual revision governance
- Production deployment hardening
- Mobile application

## User Workflow

1. Place public technical PDFs in `database/`.
2. Optionally add a matching metadata JSON sidecar.
3. Run ingestion.
4. Ask a troubleshooting question.
5. Receive a structured answer with safety/preconditions first.
6. Inspect citations, tables, figures, and page previews.
7. Run evaluation cases to measure retrieval, grounding, citations, and strictness.

## API Shape

```text
POST /ingest
  Indexes new or changed PDFs from database/.

GET /documents
  Lists indexed documents and ingestion status.

POST /retrieve
  Returns ranked evidence candidates without generating an answer.

POST /ask
  Runs decomposition, retrieval, reranking, verification, and answer generation.

POST /evaluate
  Runs the manual evaluation set and returns scores.

GET /sources/{source_id}
  Returns source preview metadata or artifact references.
```

## Answer Behavior

The system must not answer from general knowledge. If no verified evidence exists, it returns:

```text
I don't have necessary information in the given documents to answer this question.
```

For multi-part questions, the system may return `partial` only when at least one required part is supported and at least one required part is unsupported. Unsupported parts must be named explicitly.

## Response Contract

```json
{
  "status": "grounded | partial | not_found",
  "answer": {
    "summary": "...",
    "safety_preconditions": ["..."],
    "procedure": ["..."],
    "notes": ["..."],
    "limitations": ["..."],
    "claims": [
      {
        "claim": "...",
        "claim_type": "diagnosis | procedure_step | warning | limitation | specification",
        "evidence_ids": ["..."]
      }
    ]
  },
  "evidence": [
    {
      "evidence_id": "...",
      "source_element_id": "...",
      "document_title": "...",
      "page_number": 1,
      "section_path": ["..."],
      "source_type": "text | table | figure | warning | procedure | spec",
      "label": "...",
      "excerpt": "...",
      "relevance_reason": "..."
    }
  ],
  "source_previews": [
    {
      "source_element_id": "...",
      "preview_type": "table | figure | page_crop",
      "url": "/sources/..."
    }
  ],
  "confidence": {
    "level": "high | medium | low",
    "verification_reason": "...",
    "retrieval_scores": {
      "vector": 0.0,
      "keyword": 0.0,
      "rerank": 0.0
    }
  }
}
```

## Retrieval Flow

```text
User query
-> contract-validated query decomposition
-> Chroma vector retrieval
-> SQLite FTS keyword retrieval
-> Reciprocal Rank Fusion
-> local reranker
-> OpenAI evidence verification for top 3-5
-> structured answer generation from verified evidence only
```

## OpenAI Usage

Use OpenAI for:

- Figure technical captioning during ingestion
- Query decomposition
- Evidence verification for the final top candidates
- Structured final answer generation
- Text embeddings

Do not use OpenAI for:

- PDF text extraction
- Table extraction
- Broad candidate reranking
- Repeated uncached transformations

Every OpenAI call should be cached by deterministic input hash, prompt version, model, and schema version.

## Contract Gates

Every model-mediated stage must produce schema-valid output and pass business rule validation:

- Query decomposition must identify sub-questions and entities.
- Retrieval candidates must include source identity and scores.
- Verification must mark which sub-questions are answered or unsupported.
- Answer claims must map to verified evidence IDs.
- `not_found` responses must contain no evidence.

Invalid model output gets one retry with validation feedback. If it still fails, the stage returns a deterministic failure or fallback according to its contract.

## Data Handling

- Do not commit `database/` PDFs.
- Do not commit `data/` indexes or extracted artifacts.
- Do not log full document text to console.
- Store traces locally.
- Make hosted model usage explicit in configuration and docs.
- Serve source previews through the backend.
