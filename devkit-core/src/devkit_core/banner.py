from __future__ import annotations

import os

from rich.console import Console
from rich.text import Text

from .term import is_tty, terminal_width

_BLOCK = (
    "██████╗ ███████╗██╗   ██╗██╗  ██╗██╗████████╗\n"
    "██╔══██╗██╔════╝██║   ██║██║ ██╔╝██║╚══██╔══╝\n"
    "██║  ██║█████╗  ██║   ██║█████╔╝ ██║   ██║   \n"
    "██║  ██║██╔══╝  ╚██╗ ██╔╝██╔═██╗ ██║   ██║   \n"
    "██████╔╝███████╗ ╚████╔╝ ██║  ██╗██║   ██║   \n"
    "╚═════╝ ╚══════╝  ╚═══╝  ╚═╝  ╚═╝╚═╝   ╚═╝   "
)

_FRAME_TPL = (
    "┌─[ >_ devkit ]─[ {ver} ]─────────────────────────────┐\n"
    "│  cross-platform developer CLI toolbelt               │\n"
    "└──────────────────────────────────────────────────────┘"
)

_ONELINER_TPL = "░▒▓ devkit ▓▒░  >_  cross-platform developer CLI toolbelt  ·  {ver}"


def print_banner(version: str) -> None:
    """Print the appropriate banner variant based on context."""
    if not is_tty():
        return

    if os.environ.get("CI"):
        return

    console = Console()
    width = terminal_width()

    if os.environ.get("NO_COLOR") is not None:
        console.print(_ONELINER_TPL.format(ver=version), highlight=False)
        return

    if width < 50:
        line = Text()
        line.append("░▒▓ devkit ▓▒░  >_  cross-platform developer CLI toolbelt  · ", style="dim #e0e0e0")
        line.append(f"v{version}", style="#ffd700")
        console.print(line)
        return

    console.print(_BLOCK, style="bold #dc143c")
    tagline = Text()
    tagline.append("  cross-platform developer CLI toolbelt", style="#9d9d9d")
    tagline.append("  ·  ", style="#474747")
    tagline.append(f"v{version}", style="#ffd700")
    console.print(tagline)


def print_frame_banner(version: str) -> None:
    """Frame banner — optional, for use between heavy outputs."""
    if not is_tty() or os.environ.get("CI") or os.environ.get("NO_COLOR") is not None:
        return
    console = Console()
    frame = _FRAME_TPL.format(ver=version)
    console.print(frame, style="dim #e0e0e0", highlight=False)
