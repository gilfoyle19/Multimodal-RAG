## Parent PRD

`issues/prd.md`

## What to build

Enforce deterministic `partial` behavior for multi-part questions where at least one sub-question has verified support and at least one required part remains unsupported.

## Acceptance criteria

- [ ] `partial` is returned only when supported and unsupported parts both exist.
- [ ] Unsupported parts are named explicitly in the response.
- [ ] Supported claims cite verified evidence.
- [ ] Tests cover grounded, partial, and not-found boundaries.
- [ ] Partial answers do not overstate unsupported repair guidance.

## Blocked by

- Blocked by `issues/020-implement-query-decomposition-contract.md`
- Blocked by `issues/021-implement-evidence-verification-contract.md`
- Blocked by `issues/022-implement-answer-generation-contract.md`

## User stories addressed

- User story 4
- User story 13
- User story 32
- User story 38
