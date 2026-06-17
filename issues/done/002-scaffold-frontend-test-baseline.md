## Parent PRD

`issues/prd.md`

## What to build

Create the initial React, Vite, and TypeScript frontend structure with a minimal test or build baseline so future UI slices can render backend contracts predictably.

## Acceptance criteria

- [x] Frontend source structure exists for the technician-facing app.
- [x] A minimal app shell renders without depending on backend data.
- [x] TypeScript configuration is present and usable.
- [x] A minimal verification command is documented in the issue completion notes.
- [x] No unrelated product UI is introduced.

## Blocked by

None - can start immediately

## User stories addressed

- User story 27

## Completion notes

- Added a Vite React TypeScript frontend scaffold under `frontend/`.
- Added a minimal static technician console shell that does not call backend data.
- Added strict TypeScript app and Vite config files plus `npm run build` and `npm run typecheck` scripts.
- Added `npm run verify` as a dependency-free scaffold verification command for the current offline environment.
- Verification command: `cd frontend; npm run verify`.
- Checks run:
  - `cd frontend; npm run verify` passed.
  - `$env:UV_CACHE_DIR='.uv-cache'; uv run pytest` passed.
  - `$env:UV_CACHE_DIR='.uv-cache'; uv run ruff check .` passed.
  - `$env:UV_CACHE_DIR='.uv-cache'; uv run mypy .` passed.
- Frontend dependency installation is blocked in this environment: `npm install` failed because npm is running in offline cache mode and the React/Vite packages are not cached.
- Intended frontend build command after dependencies are installed: `cd frontend; npm run build`.
