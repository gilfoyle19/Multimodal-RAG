## Parent PRD

`issues/prd.md`

## What to build

Define the first backend Pydantic contracts for documents, pages, source elements, chunks, evidence candidates, verified evidence, answer status, source previews, and validation errors.

## Acceptance criteria

- [x] Contracts cover the core vocabulary in `CONTEXT.md` without embedding implementation plans there.
- [x] Answer status is constrained to `grounded`, `partial`, and `not_found`.
- [x] Source elements and evidence contracts include deterministic citation identity fields.
- [x] Unit tests cover valid payloads and schema validation failures.
- [x] Business-rule validation has an explicit home for later slices.

## Blocked by

- Blocked by `issues/001-scaffold-backend-test-baseline.md`

## User stories addressed

- User story 20
- User story 27
- User story 28
- User story 29
