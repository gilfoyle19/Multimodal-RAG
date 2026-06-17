---
name: github-to-issues
description: Import open GitHub issues into local markdown files under issues/ for Ralph or other local issue workflows. Use when the user wants GitHub issues checked from the current git repository, converted into local .md issue files, mirrored into issues/, or prepared for an AFK/Ralph loop without directly modifying GitHub.
---

# GitHub to Issues

Import open GitHub issues from the current git repository into local markdown files that Ralph can consume from `issues/`.

## Process

### 1. Confirm repository and tools

Work from the repository root.

Check that the GitHub CLI is available and authenticated:

```powershell
gh auth status
gh repo view
```

If `gh` is missing, unauthenticated, or the repository has no GitHub remote, stop and explain the blocker. Do not hand-roll GitHub API calls unless the user explicitly asks.

### 2. Fetch open GitHub issues

Fetch open issues from the current repository:

```powershell
gh issue list --state open --limit 100 --json number,title,body,labels,url,state,createdAt,updatedAt
```

If the user asks for a subset, apply the relevant `gh issue list` filters such as `--label`, `--assignee`, `--author`, or `--search`.

Do not fetch pull requests as issues. If the `gh` output includes PR-like entries, skip them.

### 3. Inspect existing local issues

Read the existing local backlog before writing files:

- `issues/*.md`
- `issues/done/*.md`

Use existing GitHub metadata to avoid duplicates. Treat an issue as already imported if any local or done file contains one of:

- `GitHub issue: #N`
- `github_issue: N`
- the issue URL

Do not overwrite a local issue file that may contain Ralph notes or partial progress.

### 4. Create local issue files

For each open GitHub issue that is not already imported, create a markdown file in `issues/`.

Use this filename pattern:

```text
issues/github-NNN-short-title.md
```

Examples:

```text
issues/github-007-add-cli-tests.md
issues/github-128-fix-login-redirect.md
```

Slug rules:

- lowercase
- hyphen-separated
- ASCII where practical
- remove punctuation that is awkward in filenames
- keep the title short enough to scan

Create the `issues/` directory if it does not exist.

### 5. Use this issue template

Write each imported issue with this structure:

```md
# GitHub #N: Issue title

GitHub issue: #N
URL: https://github.com/OWNER/REPO/issues/N
State: open
Labels: label-one, label-two
Created: YYYY-MM-DD
Updated: YYYY-MM-DD

## Source

Imported from GitHub issue #N.

## What to build

Original GitHub issue body, lightly normalized for markdown readability.

## Acceptance criteria

- [ ] Preserve explicit acceptance criteria from the GitHub issue if present.
- [ ] If none are present, derive a concise checklist from the issue body.

## Blocked by

None - can start immediately

## Ralph Notes

```

If the GitHub issue body already contains clear sections such as "Acceptance criteria", "Steps to reproduce", or "Expected behavior", preserve those headings instead of flattening them.

### 6. Keep GitHub read-only

Do not close, comment on, label, assign, or otherwise modify GitHub issues as part of this skill.

This skill only imports GitHub issues into local markdown. A separate workflow may later sync completed local files back to GitHub.

### 7. Report the import result

After writing files, summarize:

- number of GitHub issues fetched
- number of new local issue files created
- number skipped because they already existed
- any blockers, such as authentication or ambiguous duplicates

Reference created files by path.

## Ralph Compatibility

Ralph reads `issues/*.md`, so imported files must live directly under `issues/`, not only in subdirectories.

Do not move files to `issues/done/` during import. Ralph owns completion and done-file movement.

Do not run `ralph/afk.ps1` unless the user explicitly asks.
