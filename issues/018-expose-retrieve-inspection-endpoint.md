## Parent PRD

`issues/prd.md`

## What to build

Expose a `/retrieve` endpoint that returns ranked evidence candidates without answer generation so maintainers can debug retrieval separately.

## Acceptance criteria

- [ ] `/retrieve` accepts a troubleshooting query payload.
- [ ] Response includes ranked candidates, source identities, scores, and relevance metadata.
- [ ] The endpoint does not call answer generation.
- [ ] Tests cover successful retrieval, no candidates, and invalid request payloads.
- [ ] The contract matches the retrieval inspection needs in the PRD.

## Blocked by

- Blocked by `issues/017-add-local-reranker-adapter.md`

## User stories addressed

- User story 25
- User story 27
