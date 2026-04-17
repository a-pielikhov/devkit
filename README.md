# devkit

A modular, cross-platform developer CLI toolbelt. One install gives you a consistent set of commands that work identically on macOS, Linux, and Windows.

```
devkit git clean-branches "feat/*"   # delete local branches by pattern
devkit net port 3000                 # see what's on a port
devkit encode uuid                   # generate a v4 UUID
devkit file find-duplicates          # find duplicate files by hash
```

Any developer can publish a `devkit-*` package to add new command groups — see [docs/plugin-authoring.md](docs/plugin-authoring.md).

---

## Prerequisites

- Python 3.11+
- [pipx](https://pipx.pypa.io/) (recommended for end-user install)

---

## Installation

```bash
pipx install devkit-cli
```

To add optional extensions:

```bash
devkit install devkit-js
```

---

## Development setup

Each package under `devkit-*/` is installed separately in editable mode:

```bash
pip install -e devkit-core/[dev]
pip install -e devkit-cli/[dev]
pip install -e devkit-git/[dev]
pip install -e devkit-net/[dev]
pip install -e devkit-file/[dev]
pip install -e devkit-encode/[dev]
```

Then run `devkit --help` to confirm the CLI is working.

---

## Tests

```bash
cd devkit-core && pytest
```

To run all packages at once:

```bash
for pkg in devkit-core devkit-git devkit-net devkit-file devkit-encode; do
  echo "=== $pkg ===" && (cd $pkg && pytest -q)
done
```

---

## Linting and formatting

Config lives in the root `pyproject.toml`. Run from the repo root:

```bash
ruff format . && ruff check . && mypy devkit-core/src devkit-git/src devkit-net/src devkit-file/src devkit-encode/src
```

---

## Documentation

| Document | Description |
|---|---|
| [docs/architecture.md](docs/architecture.md) | Package dependency graph, install flow, plugin discovery, command dispatch — Mermaid diagrams |
| [docs/commands-reference.md](docs/commands-reference.md) | Full command reference: all flags, arguments, and exit codes |
| [docs/config-reference.md](docs/config-reference.md) | Config keys per module, defaults, and `devkit <module> config` usage |
| [docs/plugin-authoring.md](docs/plugin-authoring.md) | How to build and publish a `devkit-*` extension |

---

## Contributing

**Branch naming:** `feat/<description>` · `fix/<description>` · `chore/<description>`

**Commits:** `feat:` / `fix:` / `chore:` / `docs:` / `refactor:` + short imperative description

**PR process:**
1. Branch off `main`
2. `ruff format . && ruff check . && mypy ...` — all must pass
3. `pytest` in every affected package — all must pass
4. Open a PR against `main`; reference the AC numbers from the spec that the PR addresses

---

## License

[MIT](LICENSE)
