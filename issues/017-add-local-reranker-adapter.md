## Parent PRD

`issues/prd.md`

## What to build

Add a local reranker adapter that reranks fused evidence candidates before hosted evidence verification, keeping OpenAI calls limited to strongest candidates.

## Acceptance criteria

- [ ] Reranker interface accepts fused candidates and returns deterministic rankings.
- [ ] A fake or simple local implementation supports tests without external services.
- [ ] Rerank scores are included in retrieval confidence metadata.
- [ ] Tests cover ordering, empty input, and score propagation.
- [ ] Hosted model verification receives only the configured top candidates.

## Blocked by

- Blocked by `issues/016-implement-hybrid-retrieval-with-rrf.md`

## User stories addressed

- User story 24
- User story 25
- User story 33
