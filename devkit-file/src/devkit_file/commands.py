from __future__ import annotations

from pathlib import Path

import typer

app = typer.Typer(name="file", help="File operation helpers")


class CommandGroup:
    name = "file"
    app = app


# ── file find-duplicates ──────────────────────────────────────────────────────

@app.command("find-duplicates")
def find_duplicates(
    path: Path = typer.Argument(Path("."), help="Directory to scan (default: current)"),
    delete: bool = typer.Option(False, "--delete", help="Delete duplicates after confirmation"),
    json_: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Find files with identical content by SHA-256 hash."""
    raise NotImplementedError


# ── file find-large-files ─────────────────────────────────────────────────────

@app.command("find-large-files")
def find_large_files(
    path: Path = typer.Argument(Path("."), help="Directory to scan (default: current)"),
    min_size: str = typer.Option("1MB", "--min-size", help="Size threshold, e.g. 10MB, 500KB"),
    ext: list[str] = typer.Option([], "--ext", help="Filter by extension, e.g. .log"),
    pattern: str | None = typer.Option(None, "--pattern", help="Filter filenames by regexp"),
    top: int = typer.Option(20, "--top", help="Show top N results"),
    json_: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Find files above --min-size, sorted by size descending."""
    raise NotImplementedError
