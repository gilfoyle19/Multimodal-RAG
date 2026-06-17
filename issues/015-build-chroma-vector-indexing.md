## Parent PRD

`issues/prd.md`

## What to build

Build persistent ChromaDB vector indexing for searchable chunks while preserving SQLite as the source of truth for metadata and source identity.

## Acceptance criteria

- [ ] Vector records use stable chunk IDs that map back to SQLite metadata.
- [ ] Embeddings are produced through an adapter that can be faked in tests.
- [ ] ChromaDB persistence lives under ignored local data paths.
- [ ] Re-indexing changed documents removes stale vector entries.
- [ ] Tests verify vector ID mapping without requiring live OpenAI calls.

## Blocked by

- Blocked by `issues/008-extract-pdf-pages-and-text-source-elements.md`
- Blocked by `issues/009-extract-tables-with-whole-table-source-elements.md`
- Blocked by `issues/010-create-row-level-table-helper-chunks.md`
- Blocked by `issues/012-add-figure-caption-generation-with-cache.md`

## User stories addressed

- User story 20
- User story 22
- User story 34
