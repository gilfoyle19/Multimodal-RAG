## Parent PRD

`issues/prd.md`

## What to build

Extract figure records and local preview artifacts from PDFs so cited figures can be inspected through backend-served source previews.

## Acceptance criteria

- [x] Figure source elements or records include document, page, label, and artifact metadata.
- [x] Preview artifacts are written under ignored local data paths.
- [x] Figure extraction preserves the original figure as evidence.
- [x] Tests verify figure record persistence and preview path generation.
- [x] No generated caption is treated as the only source evidence.

## Blocked by

- Blocked by `issues/008-extract-pdf-pages-and-text-source-elements.md`

## User stories addressed

- User story 7
- User story 12
- User story 22
- User story 35
