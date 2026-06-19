## Parent PRD

`issues/prd.md`

## What to build

Implement hybrid retrieval that combines ChromaDB vector results and SQLite FTS keyword results with Reciprocal Rank Fusion into ranked evidence candidates.

## Acceptance criteria

- [x] Retrieval uses only documents with indexed status.
- [x] Vector and keyword result lists are fused with deterministic RRF behavior.
- [x] Evidence candidates include source identity and retrieval scores.
- [x] Tests cover vector-only, keyword-only, overlapping, and empty result paths.
- [x] Fault-table and specification-style candidates can map back to source elements.

## Blocked by

- Blocked by `issues/014-build-sqlite-fts-keyword-indexing.md`
- Blocked by `issues/015-build-chroma-vector-indexing.md`

## User stories addressed

- User story 9
- User story 11
- User story 12
- User story 25
