from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from rich.box import HEAVY_HEAD
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

STYLES = {
    "prompt":    "bold #dc143c",
    "path":      "#708090",
    "group":     "bold #dc143c",
    "flag":      "#ffd700",
    "value":     "#ffd700",
    "string":    "#b6e3a1",
    "success":   "bold #ffd700",
    "error":     "bold #dc143c",
    "primary":   "#e0e0e0",           # moon — full brightness
    "ink":       "#9d9d9d",           # 70% moon on black  rgba(224,224,224,0.70)
    "secondary": "#708090",           # steel
    "dim":       "#707070",           # 50% moon on black  rgba(224,224,224,0.50)
    "dim2":      "#474747",           # 32% moon on black  rgba(224,224,224,0.32)
    "border":    "#3e464f",           # 55% steel on black rgba(112,128,144,0.55)
}

_theme = Theme(STYLES)
_stdout = Console(theme=_theme)
_stderr = Console(stderr=True, theme=_theme)


def print_error(
    message: str,
    *,
    body: str | None = None,
    fix: str | None = None,
    hint: str | None = None,
    exit_code: int | None = None,
) -> None:
    _stderr.print()
    line = Text()
    line.append("  Error: ", style="error")
    line.append(message, style="primary")
    _stderr.print(line)

    if body:
        _stderr.print()
        _stderr.print(f"  [dim]{body}[/dim]")

    if fix:
        _stderr.print()
        _stderr.print(f"    [secondary]│[/secondary] [primary]{fix}[/primary]")

    if hint:
        _stderr.print()
        _stderr.print(f"  [dim]{hint}[/dim]")

    if exit_code is not None:
        _stderr.print()
        ec = Text("  exit code ", style="dim2")
        ec.append(str(exit_code), style="error")
        _stderr.print(ec)

    _stderr.print()


def print_warning(message: str) -> None:
    _stderr.print(f"[yellow]Warning:[/yellow] [primary]{message}[/primary]")


def print_tip(text: str) -> None:
    """Print a dim hint line to stdout. Silently skipped when not a TTY."""
    import sys
    if not (hasattr(sys.stdout, "isatty") and sys.stdout.isatty()):
        return
    _stdout.print(f"  [dim]Tip: {text}[/dim]")


def print_table(
    columns: list[str],
    rows: Iterable[tuple[Any, ...]],
    *,
    title: str | None = None,
) -> None:
    table = Table(
        title=title,
        show_header=True,
        header_style="bold #e0e0e0",
        border_style="#3e464f",
        box=HEAVY_HEAD,
        pad_edge=False,
        padding=(0, 1),
    )
    for col in columns:
        table.add_column(col)
    for row in rows:
        table.add_row(*[str(v) for v in row])
    _stdout.print(table)
