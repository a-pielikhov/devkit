from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

import typer

from devkit_core.output import print_error, print_table, print_warning
from devkit_core.spinner import run_with_spinner

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

    def _scan() -> tuple[list[list[Path]], int]:
        hashes: dict[str, list[Path]] = defaultdict(list)
        empty_count = 0

        def scan_dir(d: Path) -> None:
            nonlocal empty_count
            try:
                for item in d.iterdir():
                    if item.is_symlink():
                        continue
                    if item.is_dir():
                        scan_dir(item)
                    elif item.is_file():
                        try:
                            if item.stat().st_size == 0:
                                empty_count += 1
                                continue
                            h = hashlib.sha256(item.read_bytes()).hexdigest()
                            hashes[h].append(item)
                        except PermissionError:
                            print_warning(f"Permission denied: {item}")
                        except OSError:
                            print_warning(f"File modified during scan, skipping: {item}")
            except PermissionError:
                print_warning(f"Permission denied, skipping: {d}")

        scan_dir(path.resolve())
        groups = [files for files in hashes.values() if len(files) > 1]
        return groups, empty_count

    groups, empty_count = run_with_spinner(_scan, label="Scanning for duplicates...")

    if not groups:
        typer.echo("No duplicates found")
        if empty_count:
            typer.echo(f"{empty_count} empty files skipped")
        return

    if json_:
        typer.echo(
            json.dumps(
                [
                    [{"path": str(f), "name": f.name, "size": f.stat().st_size} for f in group]
                    for group in groups
                ]
            )
        )
        return

    for i, group in enumerate(groups, 1):
        typer.echo(f"\nGroup {i}:")
        print_table(
            ["Filename", "Path", "Size"],
            [(f.name, str(f.parent), str(f.stat().st_size)) for f in group],
        )
    if empty_count:
        typer.echo(f"\n{empty_count} empty files skipped")

    if delete:
        for group in groups:
            sorted_group = sorted(group, key=lambda f: len(str(f)))
            typer.echo(f"\nKeeping: {sorted_group[0]}")

        to_delete = [f for group in groups for f in sorted(group, key=lambda f: len(str(f)))[1:]]
        confirmed = typer.confirm(f"\nDelete {len(to_delete)} duplicate(s)?")
        if confirmed:
            for f in to_delete:
                f.unlink()
            typer.echo(f"Deleted {len(to_delete)} file(s)")


# ── file find-large-files ─────────────────────────────────────────────────────

_SIZE_RE = re.compile(r"^(\d+(?:\.\d+)?)\s*(B|KB|MB|GB|TB)?$", re.IGNORECASE)
_UNITS = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3, "TB": 1024**4}


def _parse_size(size_str: str) -> int:
    m = _SIZE_RE.match(size_str.strip())
    if not m:
        print_error("Invalid size format. Use e.g. 10MB, 500KB, 1GB")
        raise typer.Exit(1)
    value = float(m.group(1))
    unit = (m.group(2) or "B").upper()
    return int(value * _UNITS[unit])


def _human(size: int) -> str:
    fsize = float(size)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if fsize < 1024.0 or unit == "TB":
            return f"{fsize:.1f} {unit}"
        fsize /= 1024.0
    return f"{fsize:.1f} B"


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
    if top < 1:
        print_error("--top must be at least 1")
        raise typer.Exit(1)

    min_bytes = _parse_size(min_size)

    compiled: re.Pattern[str] | None = None
    if pattern:
        try:
            compiled = re.compile(pattern)
        except re.error as exc:
            print_error(f"Invalid pattern: {exc}")
            raise typer.Exit(1) from None

    ext_set = {e if e.startswith(".") else f".{e}" for e in ext}

    def _scan() -> list[tuple[Path, int]]:
        results: list[tuple[Path, int]] = []

        def scan_dir(d: Path) -> None:
            try:
                for item in d.iterdir():
                    if item.is_dir() and not item.is_symlink():
                        scan_dir(item)
                    elif item.is_file() or item.is_symlink():
                        try:
                            size = item.stat().st_size
                            if size < min_bytes:
                                continue
                            if ext_set and item.suffix not in ext_set:
                                continue
                            if compiled and not compiled.search(item.name):
                                continue
                            results.append((item, size))
                        except OSError:
                            pass
            except PermissionError:
                print_warning(f"Permission denied, skipping: {d}")

        scan_dir(path.resolve())
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top]

    results = run_with_spinner(_scan, label="Scanning for large files...")

    if not results:
        typer.echo("No files found matching criteria")
        return

    if json_:
        typer.echo(
            json.dumps([{"path": str(f), "size_bytes": s, "size_human": _human(s)} for f, s in results])
        )
    else:
        print_table(["Path", "Size"], [(str(f), _human(s)) for f, s in results])
