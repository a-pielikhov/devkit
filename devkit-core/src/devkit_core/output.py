from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from rich.console import Console
from rich.table import Table

_stdout = Console()
_stderr = Console(stderr=True)


def print_error(message: str) -> None:
    _stderr.print(f"[red]Error:[/red] {message}")


def print_warning(message: str) -> None:
    _stderr.print(f"[yellow]Warning:[/yellow] {message}")


def print_table(
    columns: list[str],
    rows: Iterable[tuple[Any, ...]],
    *,
    title: str | None = None,
) -> None:
    table = Table(title=title, show_header=True, header_style="bold")
    for col in columns:
        table.add_column(col)
    for row in rows:
        table.add_row(*[str(v) for v in row])
    _stdout.print(table)
