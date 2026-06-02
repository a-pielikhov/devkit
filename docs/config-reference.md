# Config reference

devkit stores all configuration in `~/.config/devkit/config.toml`. The file is managed exclusively through `devkit <module> config` subcommands — users never need to edit it directly.

Configuration is organised into per-module sections. Each module only reads its own section. The file is created on first write; if it does not exist, all defaults apply.

---

## File format

```toml
[git]
protected_branches = ["main", "master", "develop"]
default_branch = "main"

[update]
auto_check_enabled = true
auto_check_interval_days = 7
```

---

## ConfigStore API (for plugin authors)

`ConfigStore` is provided by `devkit-core` (`devkit-core/src/devkit_core/config.py`).

```python
from devkit_core import ConfigStore

store = ConfigStore()

store.get("git", "protected_branches", default=["main", "master", "develop"])
store.add("git", "protected_branches", "staging")          # appends to list
store.add("git", "protected_branches", "trunk", replace=True)  # overwrites
store.remove("git", "protected_branches", "staging")       # removes one value
store.remove("git", "protected_branches")                  # removes the key
store.remove_all("git")                                    # clears entire section
store.show("git")                                          # returns dict
```

If the config file exists but contains invalid TOML, devkit exits with code 2 and prints the parse error with the file path.

---

## devkit-git config keys

Managed via `devkit git config add / remove / show`.

| Key | Type | Default | Description |
|---|---|---|---|
| `protected_branches` | list of strings | `["main", "master", "develop"]` | Branches that `clean-branches` and `list-merged` refuse to delete without `--force` |
| `default_branch` | string | auto-detected (`main` → `master` fallback) | Default branch used by `list-merged` when no `main` or `master` exists |

### Examples

```bash
# Add a protected branch
devkit git config add protected_branches staging

# Remove a protected branch
devkit git config remove protected_branches staging

# Set a custom default branch
devkit git config add default_branch trunk

# View current config
devkit git config show

# View as JSON
devkit git config show --json

# Clear all git config
devkit git config remove --all
```

Resulting `~/.config/devkit/config.toml`:

```toml
[git]
protected_branches = ["main", "master", "develop", "staging"]
default_branch = "trunk"
```

---

## devkit update config keys

Managed via `devkit config set / get / reset`. These are core-level (global) keys, not per-module.

| Key | Type | Default | Description |
|---|---|---|---|
| `update.auto_check_enabled` | bool | `true` | Enable background update checks on every invocation |
| `update.auto_check_interval_days` | int | `7` | Minimum days between background checks |

### Examples

```bash
# Disable automatic background checks
devkit config set update.auto_check_enabled false

# Check for updates weekly (default)
devkit config set update.auto_check_interval_days 7

# View current update settings
devkit config show
```

### Update cache file

`~/.config/devkit/update-cache.json` — written by the background thread, never user-edited. Stores the last check timestamp and latest known version:

```json
{"last_check_timestamp": "2026-05-16T10:00:00Z", "latest_known_version": "v0.2.0"}
```

Delete this file to force an immediate background check on the next invocation.

---

## Other modules

`devkit-net`, `devkit-file`, and `devkit-encode` do not define configurable keys in v1. If a plugin needs user config, it follows the same pattern — declare a `config` sub-app and use `ConfigStore` with its module name as the section key. See [plugin-authoring.md](plugin-authoring.md) for details.
