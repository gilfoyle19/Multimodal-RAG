## Parent PRD

`issues/prd.md`

## What to build

Implement hybrid retrieval that combines ChromaDB vector results and SQLite FTS keyword results with Reciprocal Rank Fusion into ranked evidence candidates.

## Acceptance criteria

- [ ] Retrieval uses only documents with indexed status.
- [ ] Vector and keyword result lists are fused with deterministic RRF behavior.
- [ ] Evidence candidates include source identity and retrieval scores.
- [ ] Tests cover vector-only, keyword-only, overlapping, and empty result paths.
- [ ] Fault-table and specification-style candidates can map back to source elements.

## Blocked by

- Blocked by `issues/014-build-sqlite-fts-keyword-indexing.md`
- Blocked by `issues/015-build-chroma-vector-indexing.md`

## User stories addressed

- User story 9
- User story 11
- User story 12
- User story 25
