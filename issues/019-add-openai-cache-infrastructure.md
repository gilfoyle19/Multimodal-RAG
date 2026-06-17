## Parent PRD

`issues/prd.md`

## What to build

Implement shared OpenAI cache infrastructure keyed by deterministic input hash, model, prompt version, and schema version for model-mediated stages.

## Acceptance criteria

- [ ] Cache records are stored in SQLite.
- [ ] Cache keys include input hash, model, prompt version, and schema version.
- [ ] Cache lookup and write APIs are reusable by captioning, decomposition, verification, and answer generation.
- [ ] Tests cover cache hit, miss, write, and version separation.
- [ ] Cache behavior does not require live OpenAI calls.

## Blocked by

- Blocked by `issues/005-create-sqlite-schema-and-bootstrap.md`
- Blocked by `issues/003-add-typed-runtime-settings-and-local-path-conventions.md`

## User stories addressed

- User story 23
- User story 24
