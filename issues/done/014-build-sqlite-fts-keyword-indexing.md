## Parent PRD

`issues/prd.md`

## What to build

Build SQLite FTS5 keyword indexing for text chunks, table chunks, row helper chunks, figure captions, and metadata-enriched searchable content.

## Acceptance criteria

- [ ] FTS indexing uses SQLite and keeps SQLite as canonical metadata.
- [ ] Searchable chunks map back to source elements.
- [ ] Indexed content includes text, tables, row helpers, and figure searchable metadata.
- [ ] Tests verify keyword matches and source-element mapping.
- [ ] Re-indexing changed documents removes stale FTS entries.

## Blocked by

- Blocked by `issues/008-extract-pdf-pages-and-text-source-elements.md`
- Blocked by `issues/009-extract-tables-with-whole-table-source-elements.md`
- Blocked by `issues/010-create-row-level-table-helper-chunks.md`
- Blocked by `issues/012-add-figure-caption-generation-with-cache.md`

## User stories addressed

- User story 9
- User story 20
- User story 21
