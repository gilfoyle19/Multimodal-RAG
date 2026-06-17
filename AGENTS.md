# Agent Instructions

Agents should make small, focused changes tied to a single issue or explicit user request.

## Operational Tech Stack

- Backend language/runtime: Python, version not pinned yet.
- Backend framework: FastAPI, intended.
- Backend contracts: Pydantic, intended.
- Frontend: React + Vite + TypeScript, intended.
- Canonical metadata store: SQLite, intended.
- Keyword search: SQLite FTS5, intended.
- Vector store: ChromaDB persistent local store, intended.
- Hosted AI provider: OpenAI, intended for embeddings, figure captions, query decomposition, evidence verification, and structured answer generation.
- Local reranker: small BGE-style reranker, intended.
- Package manager: not selected yet. Do not introduce one without an issue or explicit user request.
- Test runner: not configured yet. Prefer `pytest` once Python code exists.
- Lint/format/typecheck: not configured yet.
- Runtime scripts: `ralph/once.ps1` and `ralph/afk.ps1`.

## Repository Map

- `CONTEXT.md` contains the domain glossary only.
- `docs/v1-prototype-design.md` contains the v1 product and architecture design.
- `docs/evaluation-rubric.md` contains the evaluation scoring rubric.
- `docs/adr/` contains architecture decision records.
- `reference.md` describes the local agent workflow.
- `ralph/` contains the autonomous coding loop scripts and prompt.
- `.codex/skills/` contains project-local skills used by Codex/Ralph workflows.
- `issues/` will contain local work items when generated.
- `database/` is reserved for local PDFs and must not be committed.
- `data/` is reserved for SQLite, ChromaDB, extracted artifacts, traces, and caches and must not be committed.

## Required Reading

Before editing code or docs, read:

1. The selected issue or latest user request.
2. `CONTEXT.md`.
3. Relevant docs in `docs/`, especially `docs/v1-prototype-design.md` for implementation work.
4. Existing code and tests in the area being changed.
5. Nested `AGENTS.md` files in touched folders, if any.

## Task Rules

- Work on one issue or request at a time.
- Prefer local issues from `issues/ready/` when that folder exists.
- Keep changes small and reviewable.
- Do not mix unrelated refactors with feature work.
- Preserve the contract-based approach described in `docs/v1-prototype-design.md`.
- Keep `CONTEXT.md` implementation-free. Add only durable domain vocabulary there.
- Record hard-to-reverse architecture decisions in `docs/adr/` using the existing short ADR style.
- Do not commit manuals, extracted document text, vector indexes, traces, artifacts, secrets, or `.env` files.

## Commands

Current repo commands:

```powershell
powershell -ExecutionPolicy Bypass -File ralph/once.ps1
powershell -ExecutionPolicy Bypass -File ralph/afk.ps1 -Iterations 5
```

Until project dependency files exist, there is no canonical test, lint, typecheck, build, or dev-server command. If Python code exists but no test command is configured, use the safest available fallback:

```powershell
python -m compileall .
python -m unittest
```

If a command cannot run because the project is not scaffolded yet or dependencies are missing, state that clearly.

## Testing Policy

- Use test-driven development for implementation issues when practical.
- Test behavior and contracts, not private implementation details.
- Add regression tests for bug fixes.
- Add integration tests for retrieval, verification, and answer-contract behavior when those layers exist.
- Do not weaken, delete, or skip failing tests just to pass the suite.
- Strict `grounded`, `partial`, and `not_found` behavior must be covered by tests once `/ask` exists.

## Issue Policy

- If complete, move the issue file to `issues/done/` when local issue folders exist.
- If incomplete, update the issue with what changed, what remains, blockers, checks run, and the next recommended step.
- Treat GitHub issues as read-only unless the user explicitly asks to mutate them.

## Commit Policy

Commit one coherent task at a time when the user asks for repository work or when running the Ralph loop.

Commit messages should include:

- issue id or task name
- summary of the change
- key decisions
- checks run
- follow-up notes, if any

## Prohibited Shortcuts

Do not:

- silently skip tests or checks
- hide failures behind broad exception handling
- commit secrets, private manuals, PDFs, extracted artifacts, indexes, or traces
- use general LLM knowledge for manual-grounded answers
- generate final answers without verified evidence
- put feature specs or implementation plans into `CONTEXT.md`
- introduce a new framework, package manager, database, or hosted provider without an issue or explicit user request
- mutate GitHub issues during Ralph runs without explicit instruction
- leave issue state stale after work
