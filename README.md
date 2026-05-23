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
