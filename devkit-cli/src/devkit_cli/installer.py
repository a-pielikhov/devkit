from __future__ import annotations

import sys
from pathlib import Path


def detect_os() -> str:
    """Return 'macos', 'linux', or 'windows'."""
    if sys.platform == "darwin":
        return "macos"
    if sys.platform.startswith("linux"):
        return "linux"
    if sys.platform == "win32":
        return "windows"
    raise RuntimeError(f"Unsupported platform: {sys.platform}")


def detect_install_method() -> str:
    """Return 'pipx' if running inside a pipx venv, otherwise 'pip'."""
    executable = Path(sys.executable).resolve()
    pipx_venvs = Path.home() / ".local" / "pipx" / "venvs"
    try:
        executable.relative_to(pipx_venvs)
        return "pipx"
    except ValueError:
        return "pip"


def os_bundle_package() -> str:
    return f"devkit-{detect_os()}"
