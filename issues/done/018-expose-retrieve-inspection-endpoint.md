## Parent PRD

`issues/prd.md`

## What to build

Expose a `/retrieve` endpoint that returns ranked evidence candidates without answer generation so maintainers can debug retrieval separately.

## Acceptance criteria

- [x] `/retrieve` accepts a troubleshooting query payload.
- [x] Response includes ranked candidates, source identities, scores, and relevance metadata.
- [x] The endpoint does not call answer generation.
- [x] Tests cover successful retrieval, no candidates, and invalid request payloads.
- [x] The contract matches the retrieval inspection needs in the PRD.

## Blocked by

- Blocked by `issues/017-add-local-reranker-adapter.md`

## User stories addressed

- User story 25
- User story 27

## Completion notes

- Added strict retrieval request and inspection response contracts.
- Added hybrid retrieval and local reranking orchestration backed by canonical SQLite source metadata.
- Exposed the inspection flow through `POST /retrieve` without verification or answer generation.
- Checks: 55 tests passed; Ruff passed; mypy passed; frontend verification passed.
