# Commands reference

Full reference for all `devkit` commands. General form:

```
devkit <group> <command> [arguments] [--options]
```

Top-level commands (`install`, `uninstall`, `list`) have no group prefix.

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

### devkit git clean-branches `<regexp>`

```
devkit git clean-branches <regexp> [--force] [--json]
```

Delete all local branches whose name fully matches `<regexp>`. Prints matching branches and asks for confirmation before deleting.

Never deletes the currently checked-out branch. Never deletes protected branches (configured via `devkit git config`) unless `--force` is passed.

| Flag | Description |
|---|---|
| `--force` | Also delete protected branches (never deletes current branch) |
| `--json` | Output result as JSON |
| `--help` | Show help |

**Exit codes:** 0 on success or no matches · 1 if `<regexp>` is invalid · 2 if not in a git repo

---

### devkit git sync-fork

```
devkit git sync-fork
```

Fetch from the `upstream` remote, rebase the current branch onto `upstream/main` (falls back to `upstream/master`), and push to `origin`.

Aborts before fetching if uncommitted changes are present. If rebase conflicts occur, aborts the rebase and restores original state.

| Flag | Description |
|---|---|
| `--help` | Show help |

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

```
devkit git list-merged [--delete] [--json]
```

List all local branches fully merged into `main` (auto-detects `master` as fallback). Excludes the currently checked-out branch and protected branches.

| Flag | Description |
|---|---|
| `--delete` | Print list, ask for confirmation, then delete listed branches |
| `--json` | Output branch names as JSON array |
| `--help` | Show help |

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
