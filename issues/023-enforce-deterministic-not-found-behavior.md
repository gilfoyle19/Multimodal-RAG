## Parent PRD

`issues/prd.md`

## What to build

Enforce deterministic `not_found` behavior so `/ask` skips answer generation when no verified evidence exists and returns the strict fallback message.

## Acceptance criteria

- [ ] No verified evidence results in status `not_found`.
- [ ] Answer generation is not called for `not_found`.
- [ ] The response contains the strict fallback message from the PRD.
- [ ] `not_found` responses contain no evidence or unsupported citations.
- [ ] Tests prove unsupported repair or replacement requests do not use general knowledge.

## Blocked by

- Blocked by `issues/021-implement-evidence-verification-contract.md`

## User stories addressed

- User story 3
- User story 13
- User story 31
- User story 39
