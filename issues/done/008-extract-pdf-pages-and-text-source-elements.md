## Parent PRD

`issues/prd.md`

## What to build

Extract page records and text source elements from digital PDFs, preserving document, page, section, and citation metadata needed for grounded answers.

## Acceptance criteria

- [x] Digital PDF pages are stored with stable page identity and page numbers.
- [x] Text source elements are created with citeable metadata.
- [x] Extraction does not require scanned PDF OCR.
- [x] Ingestion status reflects extraction success or failure.
- [x] Tests use small local fixtures and do not commit private manuals.

## Blocked by

- Blocked by `issues/007-implement-hash-based-ingestion-status.md`

## User stories addressed

- User story 6
- User story 20
