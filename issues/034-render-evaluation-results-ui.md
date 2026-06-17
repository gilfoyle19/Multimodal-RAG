## Parent PRD

`issues/prd.md`

## What to build

Render evaluation results in the frontend so maintainers can inspect per-case failures and aggregate quality across rubric dimensions.

## Acceptance criteria

- [ ] UI calls the `/evaluate` endpoint.
- [ ] Aggregate scores and per-case results are visible.
- [ ] Failed dimensions are easy to scan.
- [ ] Loading, empty, and error states are handled.
- [ ] Frontend tests or build checks verify evaluation rendering.

## Blocked by

- Blocked by `issues/002-scaffold-frontend-test-baseline.md`
- Blocked by `issues/033-expose-evaluate-endpoint.md`

## User stories addressed

- User story 36
- User story 38
