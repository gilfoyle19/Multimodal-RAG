## Parent PRD

`issues/prd.md`

## What to build

Create the initial FastAPI backend project structure and a minimal automated test baseline so future backend slices have a stable place to add contracts, APIs, and behavior.

## Acceptance criteria

- [x] Backend source and test directories exist with clear import boundaries.
- [x] A minimal FastAPI app exposes a health or root endpoint.
- [x] A minimal test verifies the app can be imported and the endpoint responds.
- [x] The chosen test command is documented in the issue completion notes.
- [x] No package manager or dependency workflow is introduced beyond what this issue explicitly requires.

## Blocked by

None - can start immediately

## User stories addressed

- User story 27
- User story 28

## Completion notes

- Added `src/multimodal_rag/api/app.py` with a minimal FastAPI app and `GET /health`.
- Added `tests/api/test_health.py` to import the app and verify the endpoint response.
- Configured pytest and mypy to use the `src` import boundary.
- Verification command: `$env:UV_CACHE_DIR='.uv-cache'; uv run pytest tests\api\test_health.py`
