## Parent PRD

`issues/prd.md`

## What to build

Add typed runtime settings for local paths, model/provider configuration, retrieval thresholds, and strictness settings. Establish conventions for `database/` inputs and `data/` runtime artifacts without committing private data.

## Acceptance criteria

- [x] Backend settings are typed and validated at startup or import time.
- [x] Defaults point to local `database/` and `data/` paths.
- [x] OpenAI model and cache-related settings are represented but do not require live credentials in tests.
- [x] Tests cover valid defaults and invalid configuration.
- [x] Local artifact and secret paths remain ignored by git.

## Blocked by

- Blocked by `issues/001-scaffold-backend-test-baseline.md`

## User stories addressed

- User story 23
- User story 34
- User story 35
