# PRD: Multimodal Manual Troubleshooting Prototype

## Problem Statement

Field technicians troubleshooting industrial equipment often have to search through long technical PDFs containing procedures, fault tables, warnings, schematics, figures, datasheets, quality specs, and work instructions. Standard search tools return pages or keyword matches, but they do not reliably assemble a grounded troubleshooting answer, expose the exact source evidence, or distinguish between supported, partial, and absent information.

The prototype must help a technician ask a direct troubleshooting question against a small set of loaded technical manuals and receive a deterministic, structured, source-cited answer. If the loaded documents do not contain the needed information, the system must say so instead of using general model knowledge or inventing repair guidance.

## Solution

Build an end-to-end web prototype for multimodal technical-manual RAG. The user places public digital PDFs in a local document database folder, runs ingestion, and asks troubleshooting questions through a simple web interface backed by a strong FastAPI API.

The system extracts text, tables, and figures from digital PDFs; stores source metadata and citeable source elements; builds keyword and vector indexes; retrieves evidence with hybrid search; reranks candidates locally; verifies the final top evidence with OpenAI; and generates a structured answer only from verified evidence. The answer must include status, safety/preconditions, supported claims, procedure steps when available, explicit limitations, citations, and source previews.

## User Stories

1. As a field technician, I want to ask a troubleshooting question in natural language, so that I can quickly find the relevant manual guidance.
2. As a field technician, I want the system to answer only from loaded documents, so that I can trust the answer is grounded in approved source material.
3. As a field technician, I want the system to say when information is not found, so that I do not act on unsupported advice.
4. As a field technician, I want partial answers to be clearly marked, so that I know which parts of my question are supported and which are missing.
5. As a field technician, I want warnings and prerequisites shown before procedure steps, so that I see safety-critical information before taking action.
6. As a field technician, I want source citations with document title, page, section, table, figure, or warning reference, so that I can verify the answer.
7. As a field technician, I want to inspect cited tables and figures, so that I can confirm the source evidence myself.
8. As a field technician, I want answers in a structured format rather than chatty prose, so that I can scan the result under field conditions.
9. As a field technician, I want fault-code questions to retrieve exact relevant table content, so that I do not have to manually scan large fault tables.
10. As a field technician, I want procedure questions to return only documented steps, so that the system does not invent repair instructions.
11. As a field technician, I want specification questions to cite the relevant datasheet or spec table, so that numerical values can be traced.
12. As a field technician, I want figure-related answers to show the original source figure, so that generated captions are not treated as the only evidence.
13. As a field technician, I want unsupported replacement or repair requests to be refused or marked partial, so that incomplete evidence is not overstated.
14. As a maintainer, I want to ingest PDFs from a local folder, so that the prototype can be run without a document-admin system.
15. As a maintainer, I want optional metadata sidecars for PDFs, so that document provenance can be captured when available.
16. As a maintainer, I want ingestion to skip unchanged PDFs, so that repeated indexing is predictable and efficient.
17. As a maintainer, I want changed PDFs to be re-indexed cleanly, so that stale chunks and citations are not reused.
18. As a maintainer, I want to see document ingestion status, so that failed or incomplete documents are visible.
19. As a maintainer, I want querying to use only fully indexed documents, so that answers are not based on partial ingestion state.
20. As a maintainer, I want extracted source elements stored with metadata, so that citations can be assembled deterministically.
21. As a maintainer, I want whole-table previews with row-level retrieval helpers, so that retrieval quality improves without making row fragments the main user-visible source.
22. As a maintainer, I want figure evidence bundles, so that figures can be retrieved through captions, nearby text, and preview references.
23. As a maintainer, I want OpenAI calls cached by input hash and prompt/schema version, so that repeated demo queries do not waste credits.
24. As a maintainer, I want OpenAI used selectively, so that costs are focused on high-value judgment and generation tasks.
25. As a maintainer, I want retrieval candidates inspectable before answer generation, so that retrieval failures can be debugged separately from generation failures.
26. As a maintainer, I want ask traces stored locally, so that failed answers can be diagnosed across decomposition, retrieval, ranking, verification, and generation.
27. As a developer, I want explicit API endpoints for ingestion, documents, retrieval, answering, evaluation, and source previews, so that each stage can be tested and debugged independently.
28. As a developer, I want Pydantic contracts for model-mediated stages, so that invalid or unsupported outputs cannot silently enter the pipeline.
29. As a developer, I want business-rule validation beyond model schemas, so that citations, evidence IDs, and answer statuses remain consistent.
30. As a developer, I want deterministic retry-then-fail behavior for invalid model outputs, so that the system does not guess its way through broken responses.
31. As a developer, I want `/ask` to avoid calling answer generation when no verified evidence exists, so that `not_found` behavior is enforced by code.
32. As a developer, I want query decomposition to produce sub-questions, so that multi-part questions can produce deterministic partial answers.
33. As a developer, I want local reranking before OpenAI evidence verification, so that hosted model calls are limited to the strongest candidates.
34. As a developer, I want SQLite to remain the canonical metadata store, so that ChromaDB does not become the source of truth.
35. As a developer, I want local artifacts served through the backend, so that PDFs, figures, thumbnails, and page previews are not copied into frontend assets.
36. As an evaluator, I want a manual evaluation set, so that prototype quality can be measured beyond ad hoc demos.
37. As an evaluator, I want expected source elements and forbidden claims in each evaluation case, so that grounding and strictness can be assessed.
38. As an evaluator, I want scoring for retrieval correctness, grounding, citation accuracy, strictness, partial handling, troubleshooting usefulness, safety handling, source previews, and schema compliance, so that failures are categorized.
39. As an evaluator, I want `not_found` questions in the evaluation set, so that strict refusal behavior is tested.
40. As an evaluator, I want questions covering text, tables, figures, warnings, procedures, and specifications, so that the multimodal behavior is exercised.

## Implementation Decisions

- The first deliverable is a full end-to-end vertical slice rather than an isolated ingestion, retrieval, or UI-only prototype.
- The prototype targets fewer than 10 digital PDFs stored locally.
- Scanned PDFs and full-page OCR are not part of v1.
- The backend uses FastAPI and exposes explicit endpoints for ingestion, document status, retrieval inspection, answering, source previews, and evaluation.
- The frontend uses React, Vite, and TypeScript as a thin renderer over the backend API.
- SQLite is the canonical store for documents, pages, source elements, chunks, ingestion status, provenance metadata, evaluation cases, OpenAI cache metadata, and ask traces.
- SQLite FTS5 provides keyword retrieval.
- ChromaDB provides persistent local vector retrieval and is not the canonical metadata store.
- Local filesystem storage holds original PDFs, rendered pages, figure crops, thumbnails, and other artifacts.
- OpenAI embeddings are used for text, table, figure-caption, and metadata-enriched searchable chunks.
- OpenAI is used selectively for figure technical captioning, query decomposition, final evidence verification, and structured answer generation.
- OpenAI is not used for PDF text extraction, table extraction, broad candidate reranking, or repeated uncached transformations.
- PyMuPDF is used for PDF text/layout extraction, rendering, page previews, and figure/page artifacts.
- pdfplumber is used for table extraction.
- Tables are stored as whole source elements for preview and citation.
- Row-level table helper chunks are created internally to improve retrieval.
- Figures are represented as figure evidence bundles containing the original figure, any source caption, nearby text, generated technical caption, and preview reference.
- Hybrid retrieval combines ChromaDB vector retrieval and SQLite FTS keyword retrieval.
- Reciprocal Rank Fusion merges vector and keyword results before reranking.
- A local BGE-style reranker reranks the fused candidate set before hosted verification.
- OpenAI evidence verification runs only on the final top candidates.
- Final answer generation receives only verified evidence.
- If there is no verified evidence, answer generation is skipped and the API returns a deterministic `not_found` response.
- Multi-part questions are decomposed into sub-questions before retrieval and verification.
- Partial answers are allowed only when at least one sub-question is supported and at least one sub-question is unsupported.
- Safety, caution, warning, and prerequisite source elements must be detected and elevated before procedure steps.
- Every model-mediated boundary uses explicit contracts with Pydantic validation and business-rule validation.
- Invalid model output gets one deterministic retry with validation feedback.
- If a retry still fails, the stage returns a deterministic fallback or internal error according to its contract.
- Answer claims are represented internally as structured claims mapped to verified evidence IDs.
- Every user-visible citation must link back to a source element.
- The `/ask` response includes status, answer fields, evidence, source previews, and confidence metadata.
- The strict fallback message is: "I don't have necessary information in the given documents to answer this question."
- Ingestion supports optional metadata sidecars for document provenance.
- Ingestion is hash-based and idempotent.
- `/ask` searches only documents with indexed status.
- Ask traces are stored locally for debugging and evaluation.
- Runtime configuration uses environment variables and typed settings for paths, OpenAI models, retrieval thresholds, and strictness settings.
- Local PDFs, indexes, extracted artifacts, traces, and secrets must not be committed.

## Testing Decisions

- Tests should verify external behavior and contracts, not private implementation details.
- Contract models should have unit tests for valid payloads, invalid payloads, and business-rule validation failures.
- Ingestion tests should cover digital PDF metadata handling, idempotent hash behavior, document status transitions, source element creation, table handling, and figure artifact records.
- Storage tests should verify SQLite persistence, source element relationships, FTS indexing, ChromaDB ID mapping, OpenAI cache records, and ask traces.
- Retrieval tests should verify vector/keyword candidate merging, Reciprocal Rank Fusion behavior, local reranker adapter behavior, and retrieval inspection output.
- Query decomposition tests should verify sub-question extraction and deterministic fallback behavior on invalid model output.
- Evidence verification tests should verify accepted, rejected, partial, and invalid-response paths.
- Answer generation tests should verify strict `grounded`, `partial`, and `not_found` behavior.
- Citation tests should verify that every answer claim maps to verified evidence and that invalid evidence IDs fail validation.
- API tests should cover `/ingest`, `/documents`, `/retrieve`, `/ask`, `/evaluate`, and `/sources/{source_id}` once implemented.
- Evaluation tests should cover scoring dimensions and aggregation from evaluation cases.
- Frontend tests should focus on rendering structured answer states, citations, source previews, ingestion status, and evaluation results.
- OpenAI-dependent tests should use adapters, fakes, fixtures, or recorded structured responses rather than live calls by default.
- A small manual evaluation set should be included early and expanded as sample documents are chosen.
- No existing codebase tests exist yet; the first implementation work should establish the test runner and baseline checks.

## Out of Scope

- Scanned PDF support and full-page OCR.
- Asset-specific retrieval scope or access control.
- Multi-tenant user accounts.
- Role-based permissions.
- Work-order, CMMS, ERP, or asset-management integration.
- Automatic manual revision governance.
- Production deployment hardening.
- Cloud object storage.
- Distributed ingestion queues.
- Real-time collaborative workflows.
- Mobile application.
- Industrial-standard licensing enforcement.
- Bundling third-party manuals in the repository.
- General-purpose document chat beyond loaded technical manuals.
- Using general LLM knowledge to answer unsupported troubleshooting questions.

## Further Notes

- The prototype should optimize for answer quality and hands-on usability, not offline-only operation.
- Publicly available PDFs may be used locally by the user, but provenance metadata should be captured where possible.
- The evaluation set should include 25-40 technician-style questions, including 5-10 `not_found` cases.
- Future implementation issues should be generated from this PRD after review.
- The current repository contains planning docs and workflow scaffolding but no application code or dependency manifest yet.
