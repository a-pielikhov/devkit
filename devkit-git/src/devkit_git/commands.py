from __future__ import annotations

import typer

app = typer.Typer(name="git", help="Git helpers")
config_app = typer.Typer(name="config", help="Manage git module config")
app.add_typer(config_app)


class CommandGroup:
    name = "git"
    app = app


# ── git clean-branches ────────────────────────────────────────────────────────

@app.command("clean-branches")
def clean_branches(
    regexp: str = typer.Argument(..., help="Branch name pattern (Python regexp)"),
    force: bool = typer.Option(False, "--force", help="Also delete protected branches"),
    json_: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Delete local branches matching <regexp>."""
    raise NotImplementedError


# ── git sync-fork ─────────────────────────────────────────────────────────────

@app.command("sync-fork")
def sync_fork() -> None:
    """Fetch upstream, rebase current branch, push to origin."""
    raise NotImplementedError


# ── git undo ─────────────────────────────────────────────────────────────────

@app.command("undo")
def undo() -> None:
    """Undo last commit, keep changes staged (git reset --soft HEAD~1)."""
    raise NotImplementedError


# ── git list-merged ───────────────────────────────────────────────────────────

@app.command("list-merged")
def list_merged(
    delete: bool = typer.Option(False, "--delete", help="Delete listed branches after confirmation"),
    json_: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """List local branches fully merged into main."""
    raise NotImplementedError


# ── git config ────────────────────────────────────────────────────────────────

@config_app.command("add")
def config_add(
    key: str = typer.Argument(...),
    value: str = typer.Argument(...),
    replace: bool = typer.Option(False, "--replace", help="Overwrite entire value"),
    json_: bool = typer.Option(False, "--json", help="Output resulting config as JSON"),
) -> None:
    """Add or merge a value into the git module config."""
    raise NotImplementedError


@config_app.command("remove")
def config_remove(
    key: str = typer.Argument(...),
    value: str | None = typer.Argument(None),
    all_: bool = typer.Option(False, "--all", help="Remove all git config after confirmation"),
) -> None:
    """Remove a config key or a specific value from a key."""
    raise NotImplementedError


@config_app.command("show")
def config_show(
    json_: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Show current git module config."""
    raise NotImplementedError
