## Parent PRD

`issues/prd.md`

## What to build

Add a local reranker adapter that reranks fused evidence candidates before hosted evidence verification, keeping OpenAI calls limited to strongest candidates.

## Acceptance criteria

- [x] Reranker interface accepts fused candidates and returns deterministic rankings.
- [x] A fake or simple local implementation supports tests without external services.
- [x] Rerank scores are included in retrieval confidence metadata.
- [x] Tests cover ordering, empty input, and score propagation.
- [x] Hosted model verification receives only the configured top candidates.

## Blocked by

- Blocked by `issues/016-implement-hybrid-retrieval-with-rrf.md`

## User stories addressed

- User story 24
- User story 25
- User story 33
