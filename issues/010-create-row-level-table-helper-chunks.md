## Parent PRD

`issues/prd.md`

## What to build

Create internal row-level table helper chunks to improve retrieval of fault-code and specification questions while keeping whole-table source elements as the cited user-visible source.

## Acceptance criteria

- [ ] Row helper chunks link back to their parent table source element.
- [ ] Row helpers are searchable but not exposed as primary citations.
- [ ] Chunk metadata distinguishes helper chunks from source elements.
- [ ] Tests verify row helper creation and parent table mapping.
- [ ] Retrieval-facing contracts can identify helper-derived candidates.

## Blocked by

- Blocked by `issues/009-extract-tables-with-whole-table-source-elements.md`

## User stories addressed

- User story 9
- User story 21
