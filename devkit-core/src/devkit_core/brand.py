from __future__ import annotations

import shutil
import sys

# Variant 3 color palette
_RESET = "\033[0m"
_MOD   = "\033[38;2;79;195;247m"   # cyan  #4fc3f7 — modules
_MGMT  = "\033[38;2;255;183;77m"   # amber #ffb74d — manage
_DIM   = "\033[38;2;68;85;102m"    # dim   #445566 — descriptions

LOGO_FULL = (
    "    __               __     __ __   \n"
    ".--|  |.-----.--.--.|  |--.|__|  |_ \n"
    "|  _  ||  -__|  |  ||    < |  |   _|\n"
    "|_____||_____|\\___/ |__|__||__|____|"
)

LOGO_COMPACT = "[ devkit ]"


def _color_supported() -> bool:
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def print_logo(version: str) -> None:
    cols = shutil.get_terminal_size(fallback=(80, 24)).columns
    color = _color_supported()

    logo = LOGO_FULL if cols >= 60 else LOGO_COMPACT
    if color:
        logo = f"{_MOD}{logo}{_RESET}"

    if color:
        ver_line = f"  {_MGMT}v{version}{_RESET}  {_DIM}—  cross-platform developer toolbelt{_RESET}"
    else:
        ver_line = f"  v{version}  —  cross-platform developer toolbelt"

    print(logo)
    print(ver_line)
    print()
