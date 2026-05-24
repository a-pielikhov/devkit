from __future__ import annotations

import os
import shutil
import sys


def is_tty() -> bool:
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def is_decorative_ok() -> bool:
    """True when ANSI decorations (colors, spinners, banners) should be shown."""
    return is_tty() and os.environ.get("NO_COLOR") is None and os.environ.get("CI") is None


def terminal_width() -> int:
    return shutil.get_terminal_size(fallback=(80, 24)).columns
