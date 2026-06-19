## Parent PRD

`issues/prd.md`

## What to build

Add OpenAI-backed technical caption generation for figure evidence bundles, cached by deterministic input hash, model, prompt version, and schema version.

## Acceptance criteria

- [x] Caption generation uses an adapter that can be faked in tests.
- [x] Cache lookup happens before any hosted model call.
- [x] Cache records include input hash, model, prompt version, and schema version.
- [x] Generated captions are stored as searchable metadata, not as sole evidence.
- [x] Tests cover cache hit, cache miss, and invalid adapter response behavior.

## Blocked by

- Blocked by `issues/011-extract-figure-records-and-preview-artifacts.md`

## User stories addressed

- User story 22
- User story 23
- User story 24
