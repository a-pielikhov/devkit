from __future__ import annotations

import threading
from collections.abc import Callable, Generator
from contextlib import contextmanager
from typing import TypeVar

from rich.console import Console, Group
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text

from .term import is_decorative_ok

T = TypeVar("T")

_FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"


def _spinner_suppressed() -> bool:
    return not is_decorative_ok()


def run_with_spinner(fn: Callable[[], T], *, label: str = "Working...") -> T:
    if _spinner_suppressed():
        return fn()

    with Progress(
        SpinnerColumn(spinner_name="dots", style="bold #dc143c", speed=1.1),
        TextColumn("[#e0e0e0]{task.description}"),
        console=Console(stderr=True),
        transient=True,
    ) as progress:
        progress.add_task(label)
        return fn()


@contextmanager
def live_spinner(label: str, *, cancellable: bool = False) -> Generator[Callable[[str], None], None, None]:
    """Context manager spinner with a dynamic secondary current-item line.

    Usage::

        with live_spinner("Hashing files…", cancellable=True) as update:
            for f in files:
                update(str(f))   # shows └─ /path below the spinner
                process(f)
    """
    if _spinner_suppressed():
        yield lambda _: None
        return

    _frame: list[int] = [0]
    _path: list[str] = [""]
    _stop = threading.Event()

    def _render() -> Group:
        f = _FRAMES[_frame[0] % len(_FRAMES)]
        line1 = Text()
        line1.append(f"  {f} ", style="bold #dc143c")
        line1.append(label, style="#e0e0e0")
        parts: list[Text] = [line1]
        if _path[0]:
            parts.append(Text(f"    └─ {_path[0]}", style="#474747"))
        if cancellable:
            hint = Text()
            hint.append("  Press ", style="#474747")
            hint.append("Ctrl+C", style="#707070")
            hint.append(" to cancel.", style="#474747")
            parts.append(hint)
        return Group(*parts)

    def update_path(path: str) -> None:
        _path[0] = path

    from rich.live import Live

    console = Console(stderr=True)
    with Live(_render(), console=console, refresh_per_second=12, transient=True) as live:

        def _tick() -> None:
            while not _stop.is_set():
                _frame[0] += 1
                live.update(_render())
                _stop.wait(timeout=1 / 12)

        t = threading.Thread(target=_tick, daemon=True)
        t.start()
        try:
            yield update_path
        finally:
            _stop.set()
            t.join(timeout=0.5)
