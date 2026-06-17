## Parent PRD

`issues/prd.md`

## What to build

Implement evaluation scoring for retrieval correctness, grounding, citation accuracy, strictness, partial handling, troubleshooting usefulness, safety handling, source preview quality, and structure compliance.

## Acceptance criteria

- [ ] Scoring uses the 0-2 rubric dimensions from `docs/evaluation-rubric.md`.
- [ ] Evaluation compares `/ask` output to expected case metadata.
- [ ] Aggregated results identify dimension-level failures.
- [ ] Tests cover pass, partial, and fail scoring examples.
- [ ] Scoring handles not-found and partial cases explicitly.

## Blocked by

- Blocked by `issues/025-implement-ask-orchestration.md`
- Blocked by `issues/031-create-manual-evaluation-case-format-and-fixtures.md`

## User stories addressed

- User story 36
- User story 37
- User story 38
- User story 39
- User story 40
