# Plugin authoring guide

Any developer can add new command groups to devkit by publishing a `devkit-*` package to PyPI. This guide covers everything needed to build, test, and publish an extension.

---

## How plugins work

devkit uses Python's standard `importlib.metadata` entry points. When `devkit` starts, `devkit-core` calls `entry_points(group="devkit.commands")` and loads every registered class. Each class must implement the `CommandGroup` protocol — two attributes: `name` (the group name shown in `--help`) and `app` (a `typer.Typer` instance with all subcommands registered).

---

## 1. Create the package

```
devkit-myplugin/
  pyproject.toml
  src/
    devkit_myplugin/
      __init__.py
      commands.py
  tests/
    __init__.py
    test_commands.py
```

---

## 2. `pyproject.toml`

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "devkit-myplugin"
version = "0.1.0"
description = "Short description of what this plugin does"
requires-python = ">=3.11"
dependencies = [
    "devkit-core>=0.1.0",
    "typer>=0.12",
    # add any other runtime dependencies here
]

[project.entry-points."devkit.commands"]
myplugin = "devkit_myplugin.commands:CommandGroup"

[project.optional-dependencies]
dev = [
    "pytest>=8",
    "pytest-mock>=3",
    "ruff>=0.4",
    "mypy>=1.10",
]

[tool.hatch.build.targets.wheel]
packages = ["src/devkit_myplugin"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

The `[project.entry-points."devkit.commands"]` section is what registers the plugin. The key (`myplugin`) becomes the top-level command group name. The value points to the `CommandGroup` class.

---

## 3. Implement `CommandGroup`

```python
# src/devkit_myplugin/commands.py
from __future__ import annotations

import typer
from devkit_core import command, print_error, print_table, print_warning

app = typer.Typer(name="myplugin", help="Short description shown in devkit --help")


class CommandGroup:
    name = "myplugin"
    app = app


@app.command("hello")
@command(long_running=False)
def hello(
    name: str = typer.Argument(..., help="Name to greet"),
    json_: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Greet someone."""
    if json_:
        import json
        print(json.dumps({"message": f"Hello, {name}!"}))
    else:
        print(f"Hello, {name}!")


@app.command("slow-hello")
@command(long_running=True)
def slow_hello(
    name: str = typer.Argument(..., help="Name to greet"),
    json_: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Greet someone slowly (shows a spinner)."""
    import time
    time.sleep(2)
    print(f"Hello, {name}!")
```

### Rules

| Rule | Detail |
|---|---|
| `name` must be unique | If two installed packages register the same entry point name, devkit exits with code 2 at startup |
| `app` must be a `typer.Typer` | All subcommands must be registered on it before `CommandGroup` is instantiated |
| `@command(long_running=True)` | Wraps the function to show a spinner; suppressed automatically with `--json`, in CI, or when stdout is not a TTY |
| `--json` parameter name | Use `json_: bool` (trailing underscore) so Python doesn't shadow the `json` stdlib module |
| Exit codes | 0 = success, 1 = user error (bad input), 2 = environment error (missing tool, permission denied) |

---

## 4. Use `ConfigStore` for per-module config

If your plugin needs user-configurable values, use `ConfigStore` from `devkit-core`. Config is stored in `~/.config/devkit/config.toml` under a section named after your module.

```python
from devkit_core import ConfigStore

_config = ConfigStore()

def get_my_setting(key: str, default=None):
    return _config.get("myplugin", key, default=default)
```

Expose config management via a `config` sub-app (following the same pattern as `devkit-git`):

```python
config_app = typer.Typer(name="config", help="Manage myplugin config")
app.add_typer(config_app)

@config_app.command("show")
def config_show(json_: bool = typer.Option(False, "--json")) -> None:
    """Show current myplugin config."""
    ...
```

---

## 5. Use output utilities

All output should go through `devkit-core` helpers so formatting stays consistent across plugins:

```python
from devkit_core import print_error, print_warning, print_table

# Structured data
print_table(
    columns=["Name", "Value"],
    rows=[("setting_a", "foo"), ("setting_b", "bar")],
)

# Warnings go to stderr
print_warning("something looks off but continuing")

# Errors go to stderr — then raise SystemExit
print_error("something went wrong")
raise SystemExit(1)
```

---

## 6. Test locally

```bash
# Install your plugin in editable mode into the same environment as devkit-cli
pip install -e devkit-cli/
pip install -e devkit-myplugin/[dev]

# Verify it was discovered
devkit --help        # your group should appear
devkit myplugin --help

# Run tests
cd devkit-myplugin
pytest
```

Use `typer.testing.CliRunner` to test commands without spawning a subprocess:

```python
from typer.testing import CliRunner
from devkit_myplugin.commands import app

runner = CliRunner()

def test_hello():
    result = runner.invoke(app, ["hello", "world"])
    assert result.exit_code == 0
    assert "Hello, world!" in result.output
```

---

## 7. Publish to PyPI

```bash
pip install build twine
python -m build
twine upload dist/*
```

Users install it with:

```bash
devkit install devkit-myplugin
```

`devkit install` verifies the package registers at least one `devkit.commands` entry point after install. If it doesn't, it uninstalls the package and exits with an error.
