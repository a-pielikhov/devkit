# devkit — Architecture

This document describes how the nine packages that make up devkit relate to each other, how the system is assembled at install time and at runtime, and how a command travels from the terminal to execution.

---

## 1. Package dependency graph

Shows which packages depend on which at install time.

- All command-group plugins depend on `devkit-core`
- OS bundles are convenience aggregators — they depend on `devkit-core` and all default plugins
- `devkit-cli` is the only package a user ever installs directly; it depends only on `devkit-core`

```mermaid
graph TD
    CLI["devkit-cli<br/>(pipx install devkit-cli)"]
    Core["devkit-core<br/>framework · discovery · config · utilities"]
    Bundle["devkit-macos / devkit-linux / devkit-windows<br/>(OS bundle)"]
    Git["devkit-git"]
    Net["devkit-net"]
    File["devkit-file"]
    Enc["devkit-encode"]

    CLI -->|depends on| Core
    Bundle -->|depends on| Core
    Bundle -->|depends on| Git
    Bundle -->|depends on| Net
    Bundle -->|depends on| File
    Bundle -->|depends on| Enc
    Git -->|depends on| Core
    Net -->|depends on| Core
    File -->|depends on| Core
    Enc -->|depends on| Core
```

---

## 2. Install-time flow

What happens when a user installs devkit for the first time.

`devkit-cli/src/devkit_cli/installer.py` provides `detect_os()` (uses `sys.platform`) and `detect_install_method()` (checks whether the current executable lives inside `~/.local/pipx/venvs/`).

```mermaid
flowchart TD
    A["pipx install devkit-cli"] --> B["devkit-cli installed<br/>devkit-core available"]
    B --> C{"detect_os()<br/>sys.platform"}
    C -->|darwin| D["pipx inject devkit-cli<br/>devkit-macos"]
    C -->|linux| E["pipx inject devkit-cli<br/>devkit-linux"]
    C -->|win32| F["pipx inject devkit-cli<br/>devkit-windows"]
    D & E & F --> G["OS bundle pulls in<br/>devkit-git · net · file · encode"]
    G --> H["devkit command ready"]
```

To add an optional extension afterwards:

```
devkit install devkit-js
```

---

## 3. Runtime startup — plugin discovery

What happens on every `devkit` invocation before any command runs.

`devkit-core/src/devkit_core/app.py` calls `build_app()`, which calls `discover_plugins()` from `devkit-core/src/devkit_core/discovery.py`. Plugin discovery reads all `devkit.commands` entry points registered in the Python environment via `importlib.metadata`, instantiates each `CommandGroup`, and adds each group's `typer.Typer` app as a subcommand group. If two packages register the same entry point name, startup exits with code 2. If a single package fails to load, it is skipped with a warning and the rest of the CLI remains functional.

```mermaid
sequenceDiagram
    participant User
    participant CLI as devkit-cli · main.py
    participant Core as devkit-core · build_app()
    participant EP as importlib.metadata
    participant Plugin as CommandGroup (e.g. devkit-git)

    User->>CLI: devkit <group> <command>
    CLI->>Core: build_app()
    Core->>Core: register install / uninstall / list
    Core->>EP: entry_points(group="devkit.commands")
    EP-->>Core: [git, net, file, encode, decode, ...]
    loop each entry point
        Core->>Plugin: ep.load()() → instance
        Plugin-->>Core: CommandGroup(name, app)
        Core->>Core: app.add_typer(group.app)
    end
    Core-->>CLI: assembled Typer app
    CLI->>CLI: app() — dispatch to matched command
```

### Registered entry points (v1)

| Name | Package | Class |
|---|---|---|
| `git` | `devkit-git` | `devkit_git.commands:CommandGroup` |
| `net` | `devkit-net` | `devkit_net.commands:CommandGroup` |
| `file` | `devkit-file` | `devkit_file.commands:CommandGroup` |
| `encode` | `devkit-encode` | `devkit_encode.commands:EncodeCommandGroup` |
| `decode` | `devkit-encode` | `devkit_encode.commands:DecodeCommandGroup` |

---

## 4. Command dispatch — config and spinner

What happens inside a single command invocation, showing the role of `ConfigStore` and the `@command` decorator.

The `@command(long_running=True)` decorator (defined in `devkit-core/src/devkit_core/command.py`) wraps the command function to call `run_with_spinner()` from `devkit-core/src/devkit_core/spinner.py`. The spinner is automatically suppressed when `--json` is set, stdout is not a TTY, or the `CI` / `NO_COLOR` environment variables are present. Config reads go through `ConfigStore` (`devkit-core/src/devkit_core/config.py`), backed by `~/.config/devkit/config.toml`.

```mermaid
sequenceDiagram
    participant User
    participant App as Typer app
    participant Cmd as @command decorator
    participant Spinner as run_with_spinner()
    participant Fn as command fn (e.g. clean_branches)
    participant CS as ConfigStore

    User->>App: devkit git clean-branches "feat/*"
    App->>Cmd: call wrapper(*args, **kwargs)
    Cmd->>Cmd: long_running=True and not --json?
    Cmd->>Spinner: run_with_spinner(fn, label=...)
    Spinner->>Spinner: suppress? (CI / NO_COLOR / non-TTY)
    Spinner->>Fn: fn(*args, **kwargs)
    Fn->>CS: get("git", "protected_branches")
    CS-->>Fn: ["main", "master", "develop"]
    Fn-->>User: confirmation prompt + result
    Spinner-->>User: stop spinner
```

