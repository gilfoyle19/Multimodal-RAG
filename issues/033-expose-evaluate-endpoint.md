## Parent PRD

`issues/prd.md`

## What to build

Expose a `/evaluate` endpoint that runs the manual evaluation set and returns per-case and aggregate scoring results.

## Acceptance criteria

- [ ] `/evaluate` runs configured evaluation cases.
- [ ] Response includes per-case scores and aggregate dimension scores.
- [ ] Evaluation failures are visible without crashing the whole run.
- [ ] Tests cover successful evaluation and invalid fixture behavior.
- [ ] Endpoint contract is explicit and documented by tests.

## Blocked by

- Blocked by `issues/032-implement-evaluation-scoring.md`

## User stories addressed

- User story 27
- User story 36
- User story 38
