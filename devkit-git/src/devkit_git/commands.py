from __future__ import annotations

import contextlib
import json
import re
from datetime import UTC, datetime

import typer
from git import GitCommandError, InvalidGitRepositoryError, Repo
from rich.console import Console as _Console
from rich.panel import Panel as _Panel
from rich.text import Text as _Text

from devkit_core.config import ConfigStore
from devkit_core.output import print_error, print_table, print_warning
from devkit_core.spinner import run_with_spinner

app = typer.Typer(name="git", help="Branch hygiene, fork sync, undo.")
config_app = typer.Typer(name="config", help="Manage git module config")
app.add_typer(config_app)

_config = ConfigStore()

_DEFAULT_PROTECTED = ["main", "master", "develop"]


def _relative_time(dt: datetime) -> str:
    delta = int((datetime.now(UTC) - dt.astimezone(UTC)).total_seconds())
    if delta < 3600:
        n = max(delta // 60, 1)
        return f"{n} minute{'s' if n != 1 else ''} ago"
    if delta < 86400:
        n = delta // 3600
        return f"{n} hour{'s' if n != 1 else ''} ago"
    if delta < 7 * 86400:
        n = delta // 86400
        return f"{n} day{'s' if n != 1 else ''} ago"
    if delta < 30 * 86400:
        n = delta // (7 * 86400)
        return f"{n} week{'s' if n != 1 else ''} ago"
    n = delta // (30 * 86400)
    return f"{n} month{'s' if n != 1 else ''} ago"


class CommandGroup:
    name = "git"
    app = app


def _open_repo() -> Repo:
    try:
        return Repo(".", search_parent_directories=True)
    except InvalidGitRepositoryError:
        print_error("Current directory is not a git repository")
        raise typer.Exit(2) from None


def _protected_branches() -> set[str]:
    raw = _config.get("git", "protected_branches", default=_DEFAULT_PROTECTED)
    if isinstance(raw, str):
        return {raw}
    return set(raw)


def _current_branch(repo: Repo) -> str | None:
    try:
        return str(repo.active_branch.name)
    except TypeError:
        return None


# ── git clean-branches ────────────────────────────────────────────────────────


@app.command("clean-branches")
def clean_branches(
    regexp: str = typer.Argument(
        ..., help="Branch name pattern (Python regexp by default; plain substring with --fixed-string)"
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Also delete protected branches"),
    json_: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
    fixed_string: bool = typer.Option(
        False,
        "--fixed-string",
        "-F",
        help="Treat <pattern> as a plain substring match instead of a regexp",
    ),
) -> None:
    """Delete local branches matching <pattern>.

    By default <pattern> is a Python regexp (anchored: must match the full branch name).
    Use --fixed-string / -F for a plain substring match.
    """
    if fixed_string:
        pattern = None
    else:
        try:
            pattern = re.compile(regexp)
        except re.error as exc:
            print_error(f"Invalid regexp: {exc}")
            raise typer.Exit(1) from None

    repo = _open_repo()
    current = _current_branch(repo)
    protected = _protected_branches()

    # Each entry: (name, short_hash, rel_time)
    def _scan() -> list[tuple[str, str, str]]:
        results = []
        for b in repo.branches:
            match = regexp in b.name if fixed_string else (pattern is not None and pattern.fullmatch(b.name))
            if match:
                try:
                    dt = datetime.fromtimestamp(b.commit.committed_date, tz=UTC)
                    short_hash = b.commit.hexsha[:7]
                except Exception:
                    dt = datetime.now(UTC)
                    short_hash = "unknown"
                results.append((b.name, short_hash, _relative_time(dt)))
        return results

    matching = run_with_spinner(_scan, label="Scanning branches...")

    if not matching:
        typer.echo("No branches match pattern")
        raise typer.Exit(0)

    to_delete: list[tuple[str, str, str]] = []
    skipped: list[tuple[str, str]] = []
    for name, short_hash, rel_time in matching:
        if name == current:
            skipped.append((name, "current"))
            continue
        if not force and name in protected:
            skipped.append((name, "protected"))
            continue
        to_delete.append((name, short_hash, rel_time))

    if not to_delete and not skipped:
        raise typer.Exit(0)

    console = _Console()

    # "Matched N branches against /pattern/" header
    header = _Text()
    header.append("  Matched ", style="#707070")
    header.append(str(len(matching)), style="bold #ffd700")
    header.append(" branch" + ("es" if len(matching) != 1 else ""), style="#707070")
    header.append(" against ", style="#707070")
    header.append(f"/{regexp}/", style="#b6e3a1")
    console.print()
    console.print(header)
    console.print()

    if json_:
        typer.echo(
            json.dumps(
                {
                    "deleted": [n for n, _, _ in to_delete],
                    "skipped": [{"name": n, "reason": r} for n, r in skipped],
                }
            )
        )
        raise typer.Exit(0)

    # Build panel content
    panel_body = _Text()
    for name, short_hash, rel_time in to_delete:
        panel_body.append(" ✗ ", style="#dc143c")
        panel_body.append(f"{name:<35}", style="#e0e0e0")
        panel_body.append(f" {short_hash}  {rel_time}", style="#707070")
        panel_body.append("\n")
    for name, reason in skipped:
        note = "current — protected" if reason == "current" else reason
        panel_body.append(" ✓ ", style="#474747")
        panel_body.append(f"{name}  ", style="#707070")
        panel_body.append(f"({note})", style="#707070")
        panel_body.append("\n")
    panel_body.rstrip()

    console.print(
        _Panel(
            panel_body,
            title="[bold #dc143c]branches to delete",
            border_style="#3e464f",
            padding=(0, 1),
        )
    )
    console.print()

    if not to_delete:
        raise typer.Exit(0)

    if not typer.confirm(f"  Delete {len(to_delete)} branch{'es' if len(to_delete) != 1 else ''}?"):
        raise typer.Exit(0)

    for name, _, _ in to_delete:
        repo.delete_head(name, force=True)

    result = _Text()
    result.append("\n  ✓ ", style="bold #ffd700")
    result.append(f"Deleted {len(to_delete)} branch{'es' if len(to_delete) != 1 else ''}.", style="#e0e0e0")
    if skipped:
        result.append(f" Skipped {len(skipped)} (current/protected).", style="#707070")
    console.print(result)


# ── git sync-fork ─────────────────────────────────────────────────────────────


@app.command("sync-fork")
def sync_fork() -> None:
    """Fetch upstream, rebase current branch, push to origin."""
    repo = _open_repo()

    if repo.is_dirty(untracked_files=False):
        print_error("Uncommitted changes detected. Stash or commit them first.")
        raise typer.Exit(2)

    upstream = next((r for r in repo.remotes if r.name == "upstream"), None)
    if upstream is None:
        print_error(
            "no upstream remote configured",
            body="This command rebases onto upstream/main. Add the remote with:",
            fix="git remote add upstream git@github.com:org/repo.git",
            hint="See devkit git sync-fork --help for details.",
            exit_code=2,
        )
        raise typer.Exit(2)

    run_with_spinner(upstream.fetch, label="Fetching from upstream...")

    ref_names = [ref.name for ref in upstream.refs]
    if "upstream/main" in ref_names:
        upstream_branch = "upstream/main"
    elif "upstream/master" in ref_names:
        upstream_branch = "upstream/master"
    else:
        print_error("Could not determine upstream branch (no main or master)")
        raise typer.Exit(2)

    current = _current_branch(repo) or "HEAD"

    upstream_commit = repo.commit(upstream_branch)
    merge_base = repo.merge_base(repo.head.commit, upstream_commit)
    new_count = (
        len(list(repo.iter_commits(f"{merge_base[0].hexsha}..{upstream_commit.hexsha}"))) if merge_base else 0
    )

    try:
        run_with_spinner(
            lambda: repo.git.rebase(upstream_branch), label=f"Rebasing onto {upstream_branch}..."
        )
    except GitCommandError as exc:
        conflicts = [d.a_path for d in repo.index.diff(None) if d.a_path is not None]
        with contextlib.suppress(GitCommandError):
            repo.git.rebase("--abort")
        conflict_str = " ".join(conflicts) if conflicts else "<unknown>"
        print_error(
            f"Rebase conflict on {conflict_str}. Resolve manually:\n"
            f"  git fetch upstream\n"
            f"  git rebase {upstream_branch}\n"
            f"  git rebase --continue   \u2190 after resolving each conflict\n"
            f"  git push origin {current}"
        )
        raise typer.Exit(2) from exc

    origin = next((r for r in repo.remotes if r.name == "origin"), None)
    if origin:
        run_with_spinner(lambda: origin.push(current), label="Pushing to origin...")

    typer.echo(f"Pulled in {new_count} commit(s) from {upstream_branch}")
    typer.echo(f"Synced {current} with {upstream_branch}")


# ── git undo ──────────────────────────────────────────────────────────────────


@app.command("undo")
def undo() -> None:
    """Undo last commit, keep changes staged (git reset --soft HEAD~1)."""
    repo = _open_repo()

    try:
        last_commit = repo.head.commit
    except ValueError:
        print_error("No commits to undo")
        raise typer.Exit(1) from None

    commit_hash = last_commit.hexsha[:7]
    raw_msg = last_commit.message
    commit_msg = (raw_msg.decode() if isinstance(raw_msg, bytes) else raw_msg).strip().splitlines()[0]
    is_merge = len(last_commit.parents) > 1
    has_parent = len(last_commit.parents) > 0

    if has_parent:
        repo.git.reset("--soft", "HEAD~1")
    else:
        repo.git.execute(["git", "update-ref", "-d", "HEAD"])

    typer.echo(f"Undone: [{commit_hash}] {commit_msg}")
    if is_merge:
        typer.echo("Note: The undone commit was a merge commit.")
    if not has_parent:
        typer.echo("Repository now has no commits.")


# ── git list-merged ───────────────────────────────────────────────────────────


@app.command("list-merged")
def list_merged(
    delete: bool = typer.Option(False, "--delete", help="Delete listed branches after confirmation"),
    json_: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """List local branches fully merged into main."""
    repo = _open_repo()

    default_branch_cfg: str | None = _config.get("git", "default-branch")
    branch_names = [b.name for b in repo.branches]

    if default_branch_cfg:
        default_branch = default_branch_cfg
    elif "main" in branch_names:
        default_branch = "main"
    elif "master" in branch_names:
        default_branch = "master"
    else:
        print_error("Cannot detect default branch. Use: devkit git config add default-branch trunk")
        raise typer.Exit(1)

    if default_branch not in branch_names:
        print_error(
            f"Default branch {default_branch!r} not found. Use: devkit git config add default-branch <name>"
        )
        raise typer.Exit(1)

    current = _current_branch(repo)
    protected = _protected_branches()
    protected.add(default_branch)

    def _find_merged() -> list[str]:
        raw = repo.git.branch("--merged", default_branch).strip().splitlines()
        merged_names = {b.strip().removeprefix("* ") for b in raw}
        return [name for name in merged_names if name and name not in protected and name != current]

    merged = run_with_spinner(_find_merged, label="Finding merged branches...")

    if not merged:
        typer.echo("No merged branches found")
        raise typer.Exit(0)

    if json_:
        typer.echo(json.dumps(merged))
    else:
        print_table(["Branch"], [(b,) for b in merged])

    if delete:
        if not typer.confirm(f"Delete {len(merged)} merged branch(es)?"):
            raise typer.Exit(0)
        for name in merged:
            repo.delete_head(name)
        typer.echo(f"Deleted {len(merged)} branch(es)")


# ── git config ────────────────────────────────────────────────────────────────


@config_app.command("add")
def config_add(
    key: str = typer.Argument(...),
    value: str = typer.Argument(...),
    replace: bool = typer.Option(False, "--replace", help="Overwrite entire value"),
    json_: bool = typer.Option(False, "--json", "-j", help="Output resulting config as JSON"),
) -> None:
    """Add or merge a value into the git module config."""
    _config.add("git", key, value, replace=replace)
    result = _config.show("git")
    if json_:
        typer.echo(json.dumps(result))
    else:
        typer.echo(f"Set git.{key} = {_config.get('git', key)!r}")


@config_app.command("remove")
def config_remove(
    key: str = typer.Argument(...),
    value: str | None = typer.Argument(None),
    all_: bool = typer.Option(False, "--all", help="Remove all git config after confirmation"),
) -> None:
    """Remove a config key or a specific value from a key."""
    if all_:
        if typer.confirm("Remove all git module config?"):
            _config.remove_all("git")
            typer.echo("Removed all git configuration")
        return

    existing = _config.get("git", key)
    if value is None:
        if existing is None:
            print_warning(f"Key {key!r} not found in git configuration")
            return
        _config.remove("git", key)
        typer.echo(f"Removed git.{key}")
    else:
        if existing is None:
            print_warning(f"Value {value!r} not found in git.{key}")
            return
        if isinstance(existing, list) and value not in existing:
            print_warning(f"Value {value!r} not found in git.{key}")
            return
        if not isinstance(existing, list) and existing != value:
            print_warning(f"Value {value!r} not found in git.{key}")
            return
        _config.remove("git", key, value)
        typer.echo(f"Removed {value!r} from git.{key}")


@config_app.command("show")
def config_show(
    json_: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Show current git module config."""
    result = _config.show("git")
    if not result:
        typer.echo("No configuration set")
        raise typer.Exit(0)
    if json_:
        typer.echo(json.dumps(result))
    else:
        print_table(["Key", "Value"], [(k, str(v)) for k, v in result.items()])
