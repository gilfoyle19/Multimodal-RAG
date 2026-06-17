## Parent PRD

`issues/prd.md`

## What to build

Store local ask traces that capture decomposition, retrieval, reranking, verification, answer construction, statuses, and failure reasons for debugging and evaluation.

## Acceptance criteria

- [ ] Ask traces are stored in SQLite or configured local data storage.
- [ ] Traces include enough structured data to debug retrieval and generation failures.
- [ ] Traces avoid committing or exposing private manuals or secrets.
- [ ] Tests verify trace creation for grounded, partial, and not-found asks.
- [ ] Retrieval inspection and evaluation can reference trace IDs where appropriate.

## Blocked by

- Blocked by `issues/025-implement-ask-orchestration.md`

## User stories addressed

- User story 25
- User story 26
