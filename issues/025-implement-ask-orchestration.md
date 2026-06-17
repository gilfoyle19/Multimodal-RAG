## Parent PRD

`issues/prd.md`

## What to build

Implement `/ask` orchestration across query decomposition, retrieval, reranking, verification, strict status handling, answer generation, citations, source previews, and confidence metadata.

## Acceptance criteria

- [ ] `/ask` accepts a natural-language troubleshooting question.
- [ ] The orchestration follows the retrieval flow in `docs/v1-prototype-design.md`.
- [ ] Responses support `grounded`, `partial`, and `not_found`.
- [ ] Source previews and citations are included when evidence exists.
- [ ] API tests cover grounded, partial, not-found, and invalid request paths.

## Blocked by

- Blocked by `issues/020-implement-query-decomposition-contract.md`
- Blocked by `issues/021-implement-evidence-verification-contract.md`
- Blocked by `issues/022-implement-answer-generation-contract.md`
- Blocked by `issues/023-enforce-deterministic-not-found-behavior.md`
- Blocked by `issues/024-enforce-deterministic-partial-behavior.md`

## User stories addressed

- User story 1
- User story 2
- User story 3
- User story 4
- User story 5
- User story 8
- User story 10
- User story 31
