from __future__ import annotations

import typer

BUILTIN_PACKAGES = frozenset(
    {"devkit-core", "devkit-git", "devkit-net", "devkit-file", "devkit-encode"}
)


def install(
    package: str = typer.Argument(..., help="PyPI package name to install"),
) -> None:
    """Install a devkit extension from PyPI."""
    raise NotImplementedError


def uninstall(
    package: str = typer.Argument(..., help="Package name to uninstall"),
) -> None:
    """Uninstall a devkit extension."""
    raise NotImplementedError


def list_extensions(
    json_: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """List all installed command groups."""
    raise NotImplementedError
