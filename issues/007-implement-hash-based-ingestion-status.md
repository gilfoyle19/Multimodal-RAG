## Parent PRD

`issues/prd.md`

## What to build

Track document hashes and ingestion status so unchanged PDFs are skipped, changed PDFs are re-indexed cleanly, and only fully indexed documents are queryable.

## Acceptance criteria

- [ ] Document records include content hash and ingestion status.
- [ ] Unchanged PDFs can be detected and skipped.
- [ ] Changed PDFs are marked for clean re-indexing.
- [ ] Failed or incomplete ingestion states are visible through stored status.
- [ ] Tests cover unchanged, changed, failed, and indexed status paths.

## Blocked by

- Blocked by `issues/006-implement-document-discovery-from-database.md`

## User stories addressed

- User story 16
- User story 17
- User story 18
- User story 19
