## Parent PRD

`issues/prd.md`

## What to build

Render structured `/ask` answer states for `grounded`, `partial`, and `not_found`, including safety/preconditions before procedure steps and explicit limitations.

## Acceptance criteria

- [ ] `grounded`, `partial`, and `not_found` statuses have distinct render states.
- [ ] Safety and preconditions appear before procedure steps.
- [ ] Unsupported parts and limitations are visible for partial answers.
- [ ] The strict not-found fallback is displayed without citations.
- [ ] Frontend tests cover all answer statuses.

## Blocked by

- Blocked by `issues/028-render-technician-question-flow.md`

## User stories addressed

- User story 2
- User story 3
- User story 4
- User story 5
- User story 8
- User story 13
