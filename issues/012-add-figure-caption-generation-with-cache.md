## Parent PRD

`issues/prd.md`

## What to build

Add OpenAI-backed technical caption generation for figure evidence bundles, cached by deterministic input hash, model, prompt version, and schema version.

## Acceptance criteria

- [ ] Caption generation uses an adapter that can be faked in tests.
- [ ] Cache lookup happens before any hosted model call.
- [ ] Cache records include input hash, model, prompt version, and schema version.
- [ ] Generated captions are stored as searchable metadata, not as sole evidence.
- [ ] Tests cover cache hit, cache miss, and invalid adapter response behavior.

## Blocked by

- Blocked by `issues/011-extract-figure-records-and-preview-artifacts.md`

## User stories addressed

- User story 22
- User story 23
- User story 24
