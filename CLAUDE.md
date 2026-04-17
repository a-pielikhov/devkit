# <project-slug> — CLAUDE.md

> Read context and spec from the vault at the start of every session.
> Write implementation code directly to real file paths — use git diff to review before committing.
> Use ai-output/ for generated documents only (specs, ADRs, release notes, design drafts).

---

## Context

Read these files from the vault before doing anything else in this session:
- `01-projects/<project-slug>/context.md` — stack, decisions, current stage
- `01-projects/<project-slug>/spec.md` — acceptance criteria, API shape, technical approach

The vault MCP server is pre-configured in `.claude/settings.json`.

---

## Stack

Python 3.11+, typer, rich, psutil, gitpython, importlib.metadata

---

## Structure

devkit-cli / devkit-core / devkit-macos / devkit-linux / devkit-windows
devkit-git / devkit-net / devkit-file / devkit-encode

---

## Conventions

- Write implementation code directly to real file paths in this repo
- Do not run git add or git commit unless explicitly asked
- When asked to commit, run git diff --staged first to verify what is staged
- Commit message format: `feat:` / `fix:` / `chore:` / `docs:` / `refactor:`
- Run linter and type checker before asking for code review

---

## README

A `README.md` must exist at the repo root and stay up to date. It must cover:
- What the project is and what problem it solves
- Prerequisites and installation steps
- How to run the project locally
- How to run tests
- How to run the linter and formatter
- Contribution guide (branch naming, PR process)

When adding a significant feature or changing the install/run/test process, update `README.md` in the same session.

---

## Linter and formatter

Set up linting and formatting on project initialisation based on the stack:

**Python**
- Formatter: `ruff format` (configured in `pyproject.toml`)
- Linter: `ruff check` (configured in `pyproject.toml`)
- Type checker: `mypy` (configured in `pyproject.toml`)
- Run all: `ruff format . && ruff check . && mypy .`

**TypeScript / React**
- Formatter: `prettier` (configured in `.prettierrc`)
- Linter: `eslint` (configured in `eslint.config.js`)
- Type checker: `tsc --noEmit`
- Run all: `prettier --check . && eslint . && tsc --noEmit`

Config files must be committed. Do not rely on editor-level settings alone.
Always run the full check before proposing a code review.

---

## Tests

<!-- Fill in: how to run tests for this project -->

---

## ai-output/

Gitignored. For generated **documents only** — not code.

Use it for: specs, ADRs, release notes, retro drafts, design exploration.
Do not use it for: implementation code, tests, config files.

```
ai-output/
  YYYY-MM-DD-description/
    raw/       <- exactly what Claude produced
    reviewed/  <- after your edits, ready to move to real location
```
