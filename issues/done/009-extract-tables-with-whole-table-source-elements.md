## Parent PRD

`issues/prd.md`

## What to build

Extract tables from digital PDFs as whole source elements so fault tables, datasheets, and specification tables can be cited and previewed as complete evidence.

## Acceptance criteria

- [x] Table source elements preserve whole-table content and citation metadata.
- [x] Table extraction is associated with document and page identity.
- [x] Table failures do not silently corrupt document ingestion state.
- [x] Tests cover at least one table fixture or representative parser fixture.
- [x] Whole tables remain the user-visible source, not row fragments.

## Blocked by

- Blocked by `issues/008-extract-pdf-pages-and-text-source-elements.md`

## User stories addressed

- User story 9
- User story 11
- User story 20
- User story 21
