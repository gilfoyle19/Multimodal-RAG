## Parent PRD

`issues/prd.md`

## What to build

Expose backend-served source previews for tables, figures, and page crops using source element identities rather than copying runtime artifacts into frontend assets.

## Acceptance criteria

- [ ] `GET /sources/{source_id}` or equivalent route returns preview metadata or artifact references.
- [ ] Table previews, figure previews, and page crop preview types are represented.
- [ ] Preview responses are tied to stored source elements.
- [ ] Tests cover successful preview lookup and missing source behavior.
- [ ] Local artifact paths are not exposed as unsafe filesystem paths.

## Blocked by

- Blocked by `issues/009-extract-tables-with-whole-table-source-elements.md`
- Blocked by `issues/011-extract-figure-records-and-preview-artifacts.md`

## User stories addressed

- User story 7
- User story 12
- User story 35
