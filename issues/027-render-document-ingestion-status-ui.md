## Parent PRD

`issues/prd.md`

## What to build

Render a frontend view for document ingestion status so maintainers can see discovered, indexing, indexed, failed, and skipped documents.

## Acceptance criteria

- [ ] UI calls the backend document/status API.
- [ ] Document status states are easy to scan.
- [ ] Failed or incomplete documents are visibly distinct.
- [ ] Loading and empty states are handled.
- [ ] Frontend tests or build checks verify the view renders expected states.

## Blocked by

- Blocked by `issues/002-scaffold-frontend-test-baseline.md`
- Blocked by `issues/007-implement-hash-based-ingestion-status.md`

## User stories addressed

- User story 18
