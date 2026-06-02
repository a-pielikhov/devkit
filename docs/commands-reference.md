# Commands reference

Full reference for all `devkit` commands. General form:

```
devkit <group> <command> [arguments] [--options]
```

Top-level commands (`install`, `uninstall`, `list`, `update`, `config`) have no group prefix.

**Exit codes** — consistent across all commands:

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | User error — invalid argument, value not found, bad format |
| 2 | Environment error — missing tool, permission denied, git not installed |

**`--json` flag** — available on all commands that produce structured output. Outputs pure JSON to stdout; suppresses spinner and rich formatting. Errors still go to stderr as plain text.

---

## devkit install

```
devkit install <package>
```

Install a devkit extension from PyPI into the current devkit environment.

Auto-detects install method: uses `pipx inject devkit-cli <package>` if the devkit executable is inside a pipx venv (`~/.local/pipx/venvs/`), otherwise uses `pip install <package>`.

After install, verifies the package declares at least one `devkit.commands` entry point. If not, uninstalls the package and exits 1.

| Flag | Description |
|---|---|
| `--help` | Show help |

**Exit codes:** 0 on success · 1 if package not on PyPI or no valid entry point · 2 if install command fails

---

## devkit uninstall

```
devkit uninstall <package>
```

Uninstall a devkit extension. Asks for confirmation before proceeding.

Refuses to uninstall built-in packages: `devkit-core`, `devkit-git`, `devkit-net`, `devkit-file`, `devkit-encode`.

| Flag | Description |
|---|---|
| `--help` | Show help |

**Exit codes:** 0 on success · 1 if package is built-in or not installed · 2 if uninstall command fails

---

## devkit list

```
devkit list [--json]
```

List all currently installed command groups in a table: group name, package, version, type (built-in / extension).

| Flag | Description |
|---|---|
| `--json` | Output as JSON array |
| `--help` | Show help |

---

## devkit git

### devkit git clean-branches `<pattern>`

Alias: `devkit git cb`

```
devkit git clean-branches <pattern> [--force] [--fixed-string] [--dry-run] [--json]
```

Delete all local branches whose name matches `<pattern>`. By default `<pattern>` is a Python regexp matched against the full branch name. With `--fixed-string` it is treated as a plain substring. Prints matching branches and asks for confirmation before deleting.

Never deletes the currently checked-out branch. Never deletes protected branches (configured via `devkit git config`) unless `--force` is passed.

| Flag | Short | Description |
|---|---|---|
| `--force` | `-f` | Also delete protected branches (never deletes current branch) |
| `--fixed-string` | `-F` | Treat `<pattern>` as a plain substring — skips regexp validation |
| `--dry-run` | `-n` | Show which branches would be deleted without deleting them |
| `--json` | `-j` | Output result as JSON |
| `--help` | — | Show help |

**Exit codes:** 0 on success or no matches · 1 if `<pattern>` is an invalid regexp (regexp mode only) · 2 if not in a git repo

---

### devkit git sync-fork

Alias: `devkit git sf`

```
devkit git sync-fork [--force] [--json]
```

Fetch from the `upstream` remote, rebase the current branch onto `upstream/main` (falls back to `upstream/master`), and push to `origin`.

Aborts before fetching if uncommitted changes are present. If rebase conflicts occur, aborts the rebase and restores original state.

| Flag | Short | Description |
|---|---|---|
| `--force` | `-f` | Skip confirmation prompt |
| `--json` | `-j` | Output result as JSON |
| `--help` | — | Show help |

**Exit codes:** 0 on success · 2 if `upstream` remote missing, network error, or rebase conflict

---

### devkit git undo

```
devkit git undo
```

Undo the last commit via `git reset --soft HEAD~1`. Changes remain staged.

| Flag | Description |
|---|---|
| `--help` | Show help |

**Exit codes:** 0 on success · 1 if no commits to undo · 2 if not in a git repo

---

### devkit git list-merged

Alias: `devkit git lm`

```
devkit git list-merged [--delete] [--json]
```

List all local branches fully merged into `main` (auto-detects `master` as fallback). Excludes the currently checked-out branch and protected branches.

| Flag | Short | Description |
|---|---|---|
| `--delete` | — | Print list, ask for confirmation, then delete listed branches |
| `--json` | `-j` | Output branch names as JSON array |
| `--help` | — | Show help |

**Exit codes:** 0 on success or empty list · 1 if default branch cannot be detected

---

### devkit git config add

```
devkit git config add <key> <value> [--replace] [--json]
```

Add `<value>` to `<key>` in the git module config. In merge mode (default), appends to an existing list or creates the key if absent. With `--replace`, overwrites the entire value.

| Flag | Description |
|---|---|
| `--replace` | Overwrite entire value instead of appending |
| `--json` | Output resulting config state as JSON |
| `--help` | Show help |

---

### devkit git config remove

```
devkit git config remove <key> [<value>] [--all]
```

Remove `<value>` from `<key>` (warns if not found), or remove the entire `<key>` if no value given. `--all` removes all git module config after confirmation.

| Flag | Description |
|---|---|
| `--all` | Remove all git module config after confirmation |
| `--help` | Show help |

---

### devkit git config show

```
devkit git config show [--json]
```

Print the current git module config in human-readable format.

| Flag | Description |
|---|---|
| `--json` | Output as JSON |
| `--help` | Show help |

---

## devkit net

### devkit net ip

```
devkit net ip [--json]
```

Print local IP address(es), public IP, and default gateway in a table. Lists each active network interface as a separate row. If public IP lookup fails, prints "unavailable" for that field and exits 0.

| Flag | Description |
|---|---|
| `--json` | Output all fields as JSON |
| `--help` | Show help |

---

### devkit net port `<number>`

```
devkit net port <number> [--json]
```

Print process name, PID, protocol (TCP/UDP), and state for the process using `<number>`. Lists all processes if multiple share the port.

| Flag | Description |
|---|---|
| `--json` | Output as JSON |
| `--help` | Show help |

**Exit codes:** 0 on success or port not in use · 1 if number outside 0–65535 · 2 if process info cannot be read due to permissions

---

### devkit net serve `[port]`

```
devkit net serve [port] [--open]
```

Start a static HTTP server serving files from the current directory. Default port: 8000. Exits cleanly on Ctrl+C.

| Flag | Description |
|---|---|
| `--open` | Open the serving URL in the default browser immediately after start |
| `--help` | Show help |

**Exit codes:** 0 on Ctrl+C · 1 if port outside 1–65535 · 2 if port already in use

---

### devkit net check `<host:port>`

```
devkit net check <host:port> [--timeout <seconds>] [--json]
```

Attempt a TCP connection to `<host:port>` and report open or unreachable with the reason.

| Flag | Default | Description |
|---|---|---|
| `--timeout` | 5 | Connection timeout in seconds |
| `--json` | — | Output result as JSON |
| `--help` | — | Show help |

**Exit codes:** 0 if open · 1 if unreachable or invalid format

---

## devkit encode

### devkit encode uuid

```
devkit encode uuid [--count <N>] [--json]
```

Generate one or more v4 UUIDs.

| Flag | Default | Description |
|---|---|---|
| `--count` | 1 | Number of UUIDs to generate |
| `--json` | — | Output as JSON array |
| `--help` | — | Show help |

---

### devkit encode base64 `<string>`

```
devkit encode base64 [<string>] [--json]
```

Encode `<string>` to base64. Reads from stdin if no argument is provided. Strips one trailing newline from stdin input.

| Flag | Description |
|---|---|
| `--json` | Output as JSON with `input` and `output` fields |
| `--help` | Show help |

---

### devkit encode hash `<string|file>`

```
devkit encode hash [<string|file>] [--algo <name>] [--json]
```

Compute md5, sha1, and sha256 of a string or file path. Reads from stdin if no argument given. Follows symlinks.

| Flag | Description |
|---|---|
| `--algo` | Output only one algorithm: `md5`, `sha1`, or `sha256` |
| `--json` | Output all computed hashes as JSON |
| `--help` | Show help |

**Exit codes:** 0 on success · 1 if `--algo` value is unsupported or argument is a directory

---

### devkit encode timestamp `[unix_timestamp]`

```
devkit encode timestamp [unix_timestamp] [--utc] [--json]
```

Convert a Unix timestamp to human-readable UTC and local time. Prints the current Unix timestamp if no argument given.

| Flag | Description |
|---|---|
| `--utc` | Output in UTC only, skip local time |
| `--json` | Output `unix`, `utc`, and `local` fields as JSON |
| `--help` | Show help |

**Exit codes:** 0 on success · 1 if argument is not a valid integer

---

### devkit encode format-json

```
devkit encode format-json [file] [--compact]
```

Pretty-print JSON from stdin or a file (2-space indentation). With `--compact`, output minified JSON instead.

| Flag | Description |
|---|---|
| `--compact` | Output minified JSON |
| `--help` | Show help |

**Exit codes:** 0 on success · 1 if input is not valid JSON (prints parse error with line and column)

---

## devkit decode

### devkit decode base64 `<string>`

```
devkit decode base64 [<string>] [--json]
```

Decode `<string>` from base64. Reads from stdin if no argument provided. Strips one trailing newline from stdin input.

URL-safe base64 (`-` and `_`) is not supported — exits 1 with a message explaining how to convert it.

| Flag | Description |
|---|---|
| `--json` | Output as JSON with `input` and `output` fields |
| `--help` | Show help |

**Exit codes:** 0 on success · 1 if input is not valid base64

---

### devkit decode timestamp `<datetime>`

```
devkit decode timestamp <datetime> [--tz <timezone>] [--json]
```

Convert a human-readable datetime string to a Unix timestamp. Assumes UTC if no timezone is specified.

Input must be ISO 8601 format: `YYYY-MM-DD HH:MM:SS`. Ambiguous formats (e.g. `01/02/03`) exit 1.

| Flag | Description |
|---|---|
| `--tz` | Interpret the datetime in the given timezone, e.g. `Europe/Warsaw` (IANA format) |
| `--json` | Output `datetime`, `timezone`, and `unix` fields as JSON |
| `--help` | Show help |

**Exit codes:** 0 on success · 1 if datetime cannot be parsed, timezone is unknown, or datetime falls in a DST gap

---

## devkit file

### devkit file find-duplicates `[path]`

```
devkit file find-duplicates [path] [--delete] [--json]
```

Scan `[path]` recursively (default: current directory) and find files with identical content by SHA-256 hash. Groups duplicates and prints each group as a table. Skips empty files (reports count) and does not follow symlinks.

| Flag | Description |
|---|---|
| `--delete` | Keep the file with the shortest path per group, delete the rest — asks for confirmation |
| `--json` | Output duplicate groups as JSON array |
| `--help` | Show help |

**Exit codes:** 0 on success or no duplicates found

---

### devkit file find-large-files `[path]`

```
devkit file find-large-files [path] [--min-size <size>] [--ext <ext>] [--pattern <regexp>] [--top <N>] [--json]
```

Scan `[path]` recursively (default: current directory) and list files above `--min-size`, sorted by size descending. Follows symlinks for file size.

| Flag | Default | Description |
|---|---|---|
| `--min-size` | `1MB` | Size threshold, e.g. `10MB`, `500KB`, `1GB` |
| `--ext` | — | Filter by extension, repeatable: `--ext .log --ext .zip` |
| `--pattern` | — | Filter filenames by Python regexp |
| `--top` | 20 | Show only top N results |
| `--json` | — | Output as JSON array with `path`, `size_bytes`, `size_human` fields |
| `--help` | — | Show help |

**Exit codes:** 0 on success or no files match · 1 if `--min-size` format is invalid or `--top 0`

---

## devkit update

```
devkit update [<package>] [--check] [--list] [--version <tag>] [--dry-run] [--json]
```

Upgrade devkit packages. Without arguments, upgrades all installed `devkit-*` packages after confirmation. With a package name, upgrades that package only.

Queries the GitHub Releases API for the main bundle; uses `pipx inject` for user-installed extensions.

| Flag | Short | Description |
|---|---|---|
| `--check` | — | Print version table (current vs latest) without installing anything |
| `--list` | — | List all available releases from GitHub (tag, date, title) newest-first |
| `--version <tag>` | — | Install a specific release (e.g. `v0.2.1`); exits 2 if tag not found |
| `--dry-run` | `-n` | Show what would be installed without installing |
| `--json` | `-j` | Output `--check` or `--list` result as JSON |
| `--help` | — | Show help |

**Exit codes:** 0 on success · 1 if package name not recognised · 2 if `--version <tag>` not found or GitHub API unreachable during install

**Background auto-check:** on every `devkit` invocation, a background daemon thread checks `~/.config/devkit/update-cache.json`. If the last check was more than `auto_check_interval_days` ago (default 7), it queries the GitHub Releases API and writes the result back. If a newer version is available, a notice is printed after the command output:

```
  Update available: v0.2.0 → run `devkit update` to install
```

Auto-check is non-blocking and never delays the invoking command. Configure via `devkit config`.

---

## devkit config

```
devkit config set <key> <value>
devkit config get <key>
devkit config show [--json]
devkit config reset <key>
```

Manage core-level (global) settings. Distinct from per-module config (`devkit git config`, `devkit net config`). Settings are stored in `~/.config/devkit/config.toml` under the relevant namespace.

| Subcommand | Description |
|---|---|
| `set <key> <value>` | Write a value and print confirmation |
| `get <key>` | Print the current value, or the default if not explicitly set |
| `show` | Print the full global config section as TOML |
| `show --json` / `show -j` | Print as JSON |
| `reset <key>` | Remove the explicit override, restoring the default |

Unrecognised keys are rejected with a clear error listing valid keys. See [config-reference.md](config-reference.md) for the full key list.

**Exit codes:** 0 on success · 1 if key is not recognised

---

## Command aliases

Short aliases for common commands. All flags and arguments work identically to the canonical form.

| Alias | Canonical |
|---|---|
| `devkit ls` | `devkit list` |
| `devkit enc` | `devkit encode` |
| `devkit dec` | `devkit decode` |
| `devkit git cb` | `devkit git clean-branches` |
| `devkit git lm` | `devkit git list-merged` |
| `devkit git sf` | `devkit git sync-fork` |
