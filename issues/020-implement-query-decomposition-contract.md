## Parent PRD

`issues/prd.md`

## What to build

Implement the query decomposition contract that turns a user question into deterministic sub-questions and entities for multi-part troubleshooting retrieval.

## Acceptance criteria

- [ ] Query decomposition output is validated by a Pydantic contract.
- [ ] Invalid model output gets one deterministic retry with validation feedback.
- [ ] Retry failure returns a deterministic fallback or internal error according to the contract.
- [ ] Tests use fake model responses for valid, invalid-then-valid, and invalid-twice paths.
- [ ] Multi-part questions preserve unsupported parts for later partial handling.

## Blocked by

- Blocked by `issues/018-expose-retrieve-inspection-endpoint.md`
- Blocked by `issues/019-add-openai-cache-infrastructure.md`

## User stories addressed

- User story 28
- User story 30
- User story 32
