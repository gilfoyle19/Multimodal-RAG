## Parent PRD

`issues/prd.md`

## What to build

Implement discovery of local digital PDFs placed in `database/`, including optional metadata sidecars for provenance.

## Acceptance criteria

- [ ] Discovery finds PDF documents under the configured database path.
- [ ] Matching metadata sidecars are parsed when present.
- [ ] Missing sidecars are allowed.
- [ ] Discovery records document candidates without indexing partial content.
- [ ] Tests cover PDFs with and without sidecars.

## Blocked by

- Blocked by `issues/003-add-typed-runtime-settings-and-local-path-conventions.md`
- Blocked by `issues/005-create-sqlite-schema-and-bootstrap.md`

## User stories addressed

- User story 14
- User story 15
- User story 18
