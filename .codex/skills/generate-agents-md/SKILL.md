---
name: generate-agents-md
description: "Create or update narrow, repo-specific AGENTS.md files for Codex/Ralph-style coding workflows. Use when the user asks to generate, improve, audit, or template AGENTS.md files that define operational agent instructions: tech stack, package manager, commands, issue workflow, testing expectations, commit rules, and prohibited shortcuts. Do not use for PRDs, feature specs, broad project context, architecture narratives, research notes, or CONTEXT.md generation."
---

# Generate AGENTS.md

Use this skill to create focused `AGENTS.md` files. `AGENTS.md` is an operational instruction file for coding agents, not a product document.

Keep it specific to how agents should work in the repo:

- operational tech stack
- package manager and dependency files
- canonical commands
- issue workflow
- test/check expectations
- commit rules
- safety rules
- folder-specific operational constraints

Do not include broad context, PRD content, feature specs, research notes, ADRs, product behavior, or long architecture explanations.

## Workflow

1. Inspect operational repo files.
   - Read existing `AGENTS.md`, `README.md`, `ralph/prompt.md`, issue templates, scripts, dependency files, lockfiles, CI config, and tool config.
   - Identify the package manager, test runner, lint/typecheck tools, build commands, service commands, and issue workflow.

2. Draft a concise root `AGENTS.md`.
   - Use imperative rules.
   - Name exact commands and paths.
   - Keep the file short enough to read every agent run.
   - Avoid generic advice that does not change agent behavior.

3. Add nested `AGENTS.md` files only for folders with special operational rules.
   - Good candidates: `tests/`, `src/infrastructure/`, `migrations/`, `scripts/`, `frontend/`, `api/`, `workers/`.
   - Do not create nested files for every feature.

4. Verify the result.
   - Check that referenced commands, paths, and tools exist or are explicitly marked as intended.
   - Ensure the file does not contain PRD, feature-spec, broad context, or changelog content.

## Default AGENTS.md Template

Start from this template unless the repo already has a better convention.
Customize bracketed fields to match the repository.

```md
# Agent Instructions

Agents should make small, focused changes tied to a single issue.

## Operational Tech Stack

- Language/runtime: Python [version if known]
- Package manager: `uv`
- Dependency files: [pyproject.toml / uv.lock / requirements.txt / etc.]
- Test runner: [pytest / unittest / tox / nox]
- Lint tool: [ruff / flake8 / pylint / none]
- Type checker: [mypy / pyright / none]
- Formatter: [ruff format / black / none]
- Build tool: [uv build / hatch / setuptools / none]
- Task runner/scripts: [Makefile / scripts/*.ps1 / scripts/*.sh / none]
- Runtime entry points: [CLI module / web app / worker / etc.]
- Local services: [database / cache / queue / object store / none]

## Repository Map

- `issues/` contains local work items.
- `src/` contains production code.
- `tests/` contains automated tests and fixtures.
- `scripts/` contains project commands.
- `ralph/` contains the autonomous coding loop.

Adjust this map to match the actual repository. Remove paths that do not exist.

## Required Reading

Before editing code, read:

1. The selected issue.
2. Existing code and tests in the area being changed.
3. Nested `AGENTS.md` files in touched folders, if present.

## Task Rules

- Work on one issue at a time.
- Prefer issues from `issues/ready/` when that folder exists.
- Keep changes small and reviewable.
- Do not mix unrelated refactors with feature work.
- Preserve existing project conventions.

## Commands

Use project scripts and `uv` when available.

Common Python fallbacks:

    uv run pytest
    uv run python -m unittest
    uv run python -m compileall .

If the repository does not use `uv`, use its configured package manager and do
not introduce `uv` unless the issue asks for it.

If a command cannot run, explain why.

## Testing Policy

- Test behavior, not implementation details.
- Add regression tests for bug fixes.
- Add integration tests for cross-module behavior when relevant.
- Do not weaken or delete failing tests just to pass the suite.

## Issue Policy

If complete, move the issue to `issues/done/`.

If incomplete, update the issue with:

- what changed
- what remains
- blockers
- checks run
- next recommended step

## Commit Policy

Commit one coherent task at a time.

Commit messages should include:

- issue id or task name
- summary of the change
- key decisions
- checks run
- follow-up notes, if any

## Prohibited Shortcuts

Do not:

- silently skip tests
- hide failures behind broad exception handling
- commit secrets or private data
- change public behavior without tests
- introduce a new package manager or framework without an issue asking for it
- leave issue state stale
```

## Content Rules

Include:

- operational tech stack details
- exact commands agents should run
- package manager and dependency-file expectations
- issue folder workflow
- testing and check requirements
- commit expectations
- repo-specific safety rules

Do not include:

- PRD content
- feature specifications
- broad project context
- research notes
- ADRs
- architecture narratives
- changelog entries
- long explanations of what the product does

## Nested AGENTS.md Guidance

Use nested files for local operational constraints only.

Examples:

- `tests/AGENTS.md`: fixture policy, test isolation, external service policy.
- `scripts/AGENTS.md`: script style, shell compatibility, safety rules.
- `migrations/AGENTS.md`: migration generation, rollback, and verification commands.
- `src/infrastructure/AGENTS.md`: adapter boundaries, secrets, destructive-operation rules.

Nested files should be shorter than the root file and should not repeat root rules.
