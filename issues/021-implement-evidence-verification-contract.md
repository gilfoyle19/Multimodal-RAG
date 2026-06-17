## Parent PRD

`issues/prd.md`

## What to build

Implement OpenAI-backed evidence verification for final top candidates, validating which sub-questions are supported or unsupported before answer generation.

## Acceptance criteria

- [ ] Verification receives only configured top reranked candidates.
- [ ] Verification output is schema-validated and business-rule validated.
- [ ] Accepted evidence maps to existing evidence candidate IDs.
- [ ] Unsupported sub-questions are represented explicitly.
- [ ] Tests cover accepted, rejected, partial, invalid-then-valid, and invalid-twice paths.

## Blocked by

- Blocked by `issues/018-expose-retrieve-inspection-endpoint.md`
- Blocked by `issues/019-add-openai-cache-infrastructure.md`
- Blocked by `issues/020-implement-query-decomposition-contract.md`

## User stories addressed

- User story 2
- User story 24
- User story 28
- User story 29
- User story 30
- User story 33
