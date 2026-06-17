# RALPH LOOP

You are running an autonomous Codex iteration.

# ISSUES

Local issue files from `issues/` are provided at the start of context. Parse
them to understand the open issues.

Open GitHub issues from `gh issue list` may also be provided when the GitHub CLI
is available and authenticated. Treat GitHub as read-only during the loop. Do
not close, comment on, label, assign, or otherwise mutate GitHub issues unless
explicitly instructed.

Work on AFK issues only, not HITL issues. Prefer local issue files when present
because they may contain Ralph notes, dependencies, or partial progress. If
there are no actionable local AFK issues, work from an open GitHub issue in the
provided JSON.

Recent RALPH commits are provided too. Review these to understand what work has
already been done.

If all AFK tasks are complete, output:

<promise>NO MORE TASKS</promise>

# TASK SELECTION

Pick the next task. Work on exactly one issue.

Prioritize tasks in this order:

1. Critical bugfixes
2. Development infrastructure

Getting development infrastructure like tests, types, and dev scripts ready is
an important precursor to building features.

3. Tracer bullets for new features

Tracer bullets are small slices of functionality that go through all layers of
the system, allowing you to test and validate the approach early. Build a tiny,
end-to-end slice of the feature first, then expand it.

4. Polish and quick wins
5. Refactors

# EXPLORATION

Explore the repo before editing. Read `AGENTS.md`, `CONTEXT.md`, and any docs
referenced by the selected issue when they exist.

# IMPLEMENTATION

Use /tdd to complete the task.

Make the smallest useful change for the selected task. Do not mix unrelated
refactors or cleanup into the issue.

# FEEDBACK LOOPS

Before committing, run the feedback loops:

- project-specific checks from `AGENTS.md`
- test commands defined by the repository, such as scripts, Makefile targets,
  tox, nox, pytest, or unittest
- Python lint, typecheck, format-check, or build commands configured by the
  repository
- if no project-specific command exists, use the safest standard-library
  fallback such as `python -m unittest`

If a check cannot run, explain why.

# CONTEXT UPDATE

Update `CONTEXT.md` only when the work creates durable project knowledge:
architecture, product behavior, data flow, integrations, constraints, setup, or
decisions.

Do not use `CONTEXT.md` as a routine changelog.

# COMMIT

Make a git commit.

The commit message must:

1. Include the issue/task
2. Include key decisions made
3. Include files changed
4. Include blockers or notes for the next iteration

# THE ISSUE

If the task is complete, move the issue file to `issues/done/`.

If the task came directly from a GitHub issue JSON entry and no local issue file
exists yet, create a corresponding local issue note under `issues/done/` when
complete or under `issues/` when incomplete. Include the GitHub issue number and
URL in that note.

If the task is not complete, add a note to the issue file with:

- what was done
- what remains
- blockers or next steps
- checks run

# FINAL RULES

ONLY WORK ON A SINGLE TASK.
