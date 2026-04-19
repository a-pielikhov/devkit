# devkit — CLAUDE.md

> This file provides context for subagents spawned by the vault orchestrator.
> Primary sessions always start from the vault (engineering-vault/), not this repo.
> Write implementation code directly to real file paths. Do not commit unless explicitly asked.

---

## Context

This repo is the implementation target for the `devkit` project.
Full context lives in the vault:
- `01-projects/devkit/context.md` — stack, decisions, current stage, repo path
- `01-projects/devkit/spec.md` — acceptance criteria, API shape, technical approach

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

Run from the repo root:

```bash
# Single package
cd devkit-core && uv run --with pytest pytest -q

# All packages
for pkg in devkit-core devkit-git devkit-net devkit-file devkit-encode; do
  echo "=== $pkg ===" && (cd $pkg && uv run --with pytest pytest -q)
done
```

Tests exist for `devkit-core` only at this stage. Each command group gets tests as commands are implemented.

---

## Definition of Done — Implementation

Implementation is complete when all of the following are true:

- [ ] All AC in `01-projects/devkit/spec.md` are checked off
- [ ] Linter passes with no errors
- [ ] Type checker passes with no errors
- [ ] All tests pass
- [ ] `README.md` reflects the current install, run, and test process

**Tracking AC progress:**
Check off each AC in `01-projects/devkit/spec.md` as it is implemented and verified.
You are permitted to write to that file for this purpose only.
Do not modify any other file in the vault.

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
