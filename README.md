# devkit

```
    __               __     __ __   
.--|  |.-----.--.--.|  |--.|__|  |_ 
|  _  ||  -__|  |  ||    < |  |   _|
|_____||_____|\___ / |__|__||__|____|
```

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
- [gh CLI](https://cli.github.com/) authenticated (`gh auth login`) — required for the install steps below

---

## Installation

Download the wheels from the [latest release](../../releases/latest) and install with pipx:

```bash
# 1. Download all wheels from the latest release (requires gh CLI + repo access)
gh release download --repo OWNER/devkit --dir /tmp/devkit-wheels

# 2. Install — installs devkit-cli directly from wheel (bypasses PyPI name conflict);
#    devkit-* dependencies resolved from local wheels, typer/rich/psutil fetched from PyPI
pipx install "$(ls /tmp/devkit-wheels/devkit_cli-*.whl)" \
  --pip-args="--find-links=/tmp/devkit-wheels"

# 3. Verify
devkit --help
```

Replace `OWNER` with the GitHub organisation or username where the repo lives.

> **Note:** This project is distributed via GitHub Releases. PyPI publish is planned once the API is stable.

---

## Shell tab completion

Run once to install completion for your shell:

    devkit --install-completion

Restart your shell (or run `source ~/.zshrc` / `source ~/.bashrc`) for completions to take effect.

---

## Development setup

Prerequisites: Python 3.11+, [uv](https://docs.astral.sh/uv/), [Docker](https://docs.docker.com/get-docker/) (for `make dev`).

All dev tasks go through `make` — no separate scripts to remember.

```bash
make init                        # one-time setup: sync venv + install git hooks
make run ARGS="git list-merged"  # run a dev command without entering a shell
make dev                         # launch an isolated dev shell inside Docker
make dev-clean                   # remove the dev image + venv volume (force rebuild)
```

`make dev` runs a Docker container with the workspace mounted — edits to `devkit-*/src/` are live immediately, no rebuild needed. The container's venv is stored in a named Docker volume (`devkit-dev-venv`) so it persists between sessions.

---

## Tests

```bash
make test        # run all packages
```

Tests also run automatically on every `git commit` via the pre-commit hook installed by `make init`.

---

## Linting and formatting

```bash
make check       # fmt + lint + type + test (full CI equivalent)
make fmt         # ruff format check only
make lint        # ruff lint only
make type        # mypy only
make fix         # auto-fix formatting and lint issues
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
2. `make check` — all must pass (format, lint, type, tests)
3. Open a PR against `main`; reference the AC numbers from the spec that the PR addresses

---

## License

[MIT](LICENSE)
