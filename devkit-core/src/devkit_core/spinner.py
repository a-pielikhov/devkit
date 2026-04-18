from __future__ import annotations

import os
import sys
from collections.abc import Callable
from typing import TypeVar

from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner as RichSpinner

T = TypeVar("T")


def _spinner_suppressed() -> bool:
    return (
        not sys.stdout.isatty() or os.environ.get("NO_COLOR") is not None or os.environ.get("CI") is not None
    )


def run_with_spinner(fn: Callable[[], T], *, label: str = "Working...") -> T:
    if _spinner_suppressed():
        return fn()

    console = Console(stderr=True)
    with Live(RichSpinner("dots", text=label), console=console, refresh_per_second=10):
        return fn()
