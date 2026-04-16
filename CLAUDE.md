# devkit — CLAUDE.md

> Read context and spec from the vault at the start of every session.
> Generated files go to `ai-output/` — never commit directly.

---

## Context

The vault MCP server is pre-configured in `.claude/settings.json`.
At the start of every session, tell Claude to read:

> "Read `01-projects/devkit/context.md` from the vault."
> "Read `01-projects/devkit/spec.md` from the vault."

These are the source of truth for stack, decisions, acceptance criteria, and scope.

---

## Stack

<!-- Fill in from context.md after creation -->

---

## Structure

<!-- Fill in from context.md after creation -->

---

## Conventions

- All AI-generated scaffolding goes to `ai-output/YYYY-MM-DD-<description>/raw/` first
- Review before moving to real location — never commit from `ai-output/` directly
- Commit message format: `feat:` / `fix:` / `chore:` / `docs:` / `refactor:`
- Run linter and type checker before asking for code review

---

## Tests

<!-- Fill in: how to run tests for this project -->

---

## ai-output/

Gitignored. Structure:

```
ai-output/
  YYYY-MM-DD-description/
    raw/       <- exactly what Claude produced
    reviewed/  <- after your edits, ready to move to real location
```
