## Parent PRD

`issues/prd.md`

## What to build

Implement shared OpenAI cache infrastructure keyed by deterministic input hash, model, prompt version, and schema version for model-mediated stages.

## Acceptance criteria

- [x] Cache records are stored in SQLite.
- [x] Cache keys include input hash, model, prompt version, and schema version.
- [x] Cache lookup and write APIs are reusable by captioning, decomposition, verification, and answer generation.
- [x] Tests cover cache hit, miss, write, and version separation.
- [x] Cache behavior does not require live OpenAI calls.

## Blocked by

- Blocked by `issues/005-create-sqlite-schema-and-bootstrap.md`
- Blocked by `issues/003-add-typed-runtime-settings-and-local-path-conventions.md`

## User stories addressed

- User story 23
- User story 24

## Completion notes

- Added a reusable SQLite-backed cache with deterministic key dimensions and canonical input hashing.
- Migrated figure captioning from private cache SQL to the shared cache API.
- Verified cache miss, durable write/hit, key-dimension separation, deterministic hashing, and caption integration without live OpenAI calls.
- Checks: 62 tests passed; Ruff passed; mypy passed; frontend scaffold verification passed.
