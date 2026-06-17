## Parent PRD

`issues/prd.md`

## What to build

Create the SQLite bootstrap layer and initial schema for documents, pages, source elements, chunks, OpenAI cache metadata, evaluation cases, and ask traces.

## Acceptance criteria

- [ ] SQLite is treated as the canonical metadata store.
- [ ] Schema creation is deterministic and can run against a fresh local database.
- [ ] Tables include stable IDs and relationships needed by contracts.
- [ ] Tests verify schema bootstrap and basic persistence.
- [ ] Runtime database files are stored under ignored local data paths.

## Blocked by

- Blocked by `issues/003-add-typed-runtime-settings-and-local-path-conventions.md`
- Blocked by `issues/004-define-core-domain-contracts.md`

## User stories addressed

- User story 20
- User story 23
- User story 26
- User story 34
