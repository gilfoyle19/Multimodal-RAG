# Agentic Workflow Reference

This reference maps the project workflow to focused rules and skills. Keep
`AGENTS.md` stable and repo-specific; use these as task-specific skills or
references when a stage needs extra decision pressure.

## Workflow

```text
IDEA
  -> /grill-me
  -> /grill-with-docs
  -> /write-a-prd
  -> /prd-to-issues
  -> ralph loop
  -> QA
```

## Loading Rule

Use one primary rule set or skill per task. Add a second only when the task
clearly spans two concerns, such as architecture plus data reliability.

Prefer:

- `mini` for normal skill bodies and day-to-day work
- `full` for deep review, audit, or architecture sessions
- `nano` only for tiny always-on project context

Do not load many overlapping book rules into the same agent run.

## Recommended Always-On Context

Use `AGENTS.md` for:

- repository map
- required reading
- task selection rules
- feedback-loop commands
- issue movement rules
- commit policy
- security/data constraints
- prohibited shortcuts

If using a book-derived always-on rule, keep it tiny. The best default is:

```text
the-pragmatic-programmer.nano
```

Use it only if the repo lacks strong engineering judgment rules already.

## Stage-to-Skill Map

### IDEA

Use:

- `domain-driven-design-distilled.mini`
- `a-philosophy-of-software-design.mini`

Purpose:

- clarify the domain
- identify subdomains and boundaries
- test whether the idea has a simple design center
- reduce accidental complexity before planning

### /grill-me

Use:

- `a-philosophy-of-software-design.mini`
- `domain-driven-design-distilled.mini`

Add when relevant:

- `release-it.mini` for production-risk questioning
- `designing-data-intensive-applications.mini` for data-heavy systems

Purpose:

- pressure-test assumptions
- challenge module/API shape
- identify hidden complexity
- expose operational and data risks early

### /grill-with-docs

Use:

- `domain-driven-design-distilled.mini`
- `a-philosophy-of-software-design.mini`

Add when relevant:

- `designing-data-intensive-applications.mini`
- `clean-architecture.mini`
- `release-it.mini`

Purpose:

- extract durable decisions from docs
- separate requirements from assumptions
- identify open questions
- produce PRD-ready notes
- connect external research to system boundaries

### /write-a-prd

Use:

- `domain-driven-design-distilled.mini`

Add when relevant:

- `release-it.mini` for non-functional requirements
- `designing-data-intensive-applications.mini` for data, indexing, queues, or RAG
- `clean-architecture.mini` for boundary-heavy products

Purpose:

- turn resolved intent into product requirements
- define user stories and acceptance criteria
- capture constraints and out-of-scope items
- surface architecture-sensitive decisions without over-designing

### /prd-to-issues

Use:

- `clean-architecture.mini`
- `a-philosophy-of-software-design.mini`

Add when relevant:

- `designing-data-intensive-applications.mini`
- `patterns-of-enterprise-application-architecture.mini`

Purpose:

- split PRDs into independently workable issues
- preserve boundaries and dependency direction
- create tracer-bullet issues before broad feature expansion
- avoid issues that require large, tangled changes

### Ralph Loop

Use by default:

- `tdd`

Use only when the selected issue needs it:

- `code-complete.mini` for implementation discipline
- `clean-architecture.mini` for boundary changes
- `refactoring.mini` for explicit refactor tasks
- `working-effectively-with-legacy-code.mini` for weakly tested code
- `designing-data-intensive-applications.mini` for data semantics
- `release-it.mini` for resilience or operational behavior

Purpose:

- complete one issue at a time
- use red-green-refactor
- add tests before or alongside behavior changes
- keep commits small and coherent
- avoid pulling architecture rules into routine implementation unless needed

### QA

Use:

- `release-it.mini`
- `code-complete.mini`

Add when relevant:

- `designing-data-intensive-applications.mini` for data correctness
- `clean-code.mini` for readability and maintainability review
- `working-effectively-with-legacy-code.mini` for regression-prone areas

Purpose:

- look for failure modes
- verify tests and checks
- review observability, retries, timeouts, and recovery paths
- identify risky hidden coupling
- confirm issue acceptance criteria are actually satisfied

## Software-Type Defaults

### General Python Project

Default:

- `tdd`
- `code-complete.mini`

Add:

- `clean-architecture.mini` for module boundaries
- `refactoring.mini` for cleanup tasks
- `working-effectively-with-legacy-code.mini` when tests are missing

### Web Application

Default:

- `clean-architecture.mini`
- `code-complete.mini`

Add:

- `release-it.mini` for production behavior
- `domain-driven-design-distilled.mini` for complex business domains

### Data Pipeline

Default:

- `designing-data-intensive-applications.mini`
- `release-it.mini`

Add:

- `working-effectively-with-legacy-code.mini` for untested pipeline changes
- `clean-architecture.mini` for adapter and boundary decisions

### AI or RAG System

Default:

- `designing-data-intensive-applications.mini`
- `release-it.mini`
- `a-philosophy-of-software-design.mini`

Add:

- `domain-driven-design-distilled.mini` for product/domain modeling
- `clean-architecture.mini` for provider, storage, and retrieval boundaries

### Legacy Codebase

Default:

- `working-effectively-with-legacy-code.mini`
- `refactoring.mini`

Add:

- `code-complete.mini` after characterization tests exist

## Anti-Patterns

Avoid:

- putting book summaries directly into `AGENTS.md`
- loading every rule set into every agent run
- using architecture rules for tiny bugfixes
- using refactoring rules while adding unrelated features
- letting Ralph choose from HITL issues
- skipping tests because the selected skill is planning-focused
- updating `CONTEXT.md` as a changelog

## Source

This reference is based on the `agent-rules-books` approach: use focused
Markdown rule sets as skills, prefer `mini` for normal work, reserve `full` for
deep sessions, and keep `nano` for tiny always-on context.
