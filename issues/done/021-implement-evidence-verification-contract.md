## Parent PRD

`issues/prd.md`

## What to build

Implement OpenAI-backed evidence verification for final top candidates, validating which sub-questions are supported or unsupported before answer generation.

## Acceptance criteria

- [x] Verification receives only configured top reranked candidates.
- [x] Verification output is schema-validated and business-rule validated.
- [x] Accepted evidence maps to existing evidence candidate IDs.
- [x] Unsupported sub-questions are represented explicitly.
- [x] Tests cover accepted, rejected, partial, invalid-then-valid, and invalid-twice paths.

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

## Completion notes

- Added a fakeable OpenAI evidence-verification boundary with versioned SQLite caching.
- Enforced configured shortlist limits, candidate and sub-question reference integrity, and complete supported/unsupported classification.
- Invalid output receives one deterministic validation-feedback retry; a second invalid response raises a deterministic stage error.
- Checks: 72 tests passed; Ruff passed; mypy passed; frozen uv sync passed; frontend verification passed.
