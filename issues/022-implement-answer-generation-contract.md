## Parent PRD

`issues/prd.md`

## What to build

Implement structured answer generation from verified evidence only, including safety or preconditions, supported claims, procedure steps, limitations, citations, and confidence metadata.

## Acceptance criteria

- [ ] Answer generation receives only verified evidence.
- [ ] Output matches the `/ask` response contract from the prototype design.
- [ ] Every claim maps to one or more verified evidence IDs.
- [ ] Safety and preconditions are elevated before procedure steps.
- [ ] Tests cover valid answers, invalid evidence references, and invalid model output retry behavior.

## Blocked by

- Blocked by `issues/021-implement-evidence-verification-contract.md`

## User stories addressed

- User story 2
- User story 5
- User story 6
- User story 8
- User story 10
- User story 28
- User story 29
