from __future__ import annotations

import importlib
import json
import subprocess
import sys
from importlib.metadata import entry_points, packages_distributions
from pathlib import Path
from typing import Any

import typer

from .discovery import discover_plugins
from .output import print_error, print_table
from .spinner import run_with_spinner

BUILTIN_PACKAGES = frozenset({"devkit-core", "devkit-git", "devkit-net", "devkit-file", "devkit-encode"})


def _detect_install_method() -> str:
    executable = Path(sys.executable).resolve()
    pipx_venvs = Path.home() / ".local" / "pipx" / "venvs"
    try:
        executable.relative_to(pipx_venvs)
        return "pipx"
    except ValueError:
        return "pip"


def install(
    package: str = typer.Argument(..., help="PyPI package name to install"),
) -> None:
    """Install a devkit extension from PyPI."""
    method = _detect_install_method()

    def _do_install() -> None:
        if method == "pipx":
            result = subprocess.run(
                ["pipx", "inject", "devkit-cli", package],
                capture_output=True,
                text=True,
            )
        else:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", package],
                capture_output=True,
                text=True,
            )
        if result.returncode != 0:
            stderr = result.stderr.lower()
            if "no matching distribution" in stderr or "not found" in stderr:
                print_error(f"{package!r} is not found on PyPI")
                raise typer.Exit(1)
            print_error(f"Install failed:\n{result.stderr.strip()}")
            raise typer.Exit(2)

    run_with_spinner(_do_install, label=f"Installing {package}...")

    importlib.invalidate_caches()
    eps = entry_points(group="devkit.commands")
    new_groups = [ep for ep in eps if ep.dist is not None and ep.dist.name == package]

    if not new_groups:
        subprocess.run(
            [sys.executable, "-m", "pip", "uninstall", "-y", package],
            capture_output=True,
        )
        print_error(f"{package!r} is not a valid devkit extension (no devkit.commands entry point found)")
        raise typer.Exit(1)

    typer.echo("Installed command groups:")
    for ep in new_groups:
        typer.echo(f"  {ep.name}")


def uninstall(
    package: str = typer.Argument(..., help="Package name to uninstall"),
) -> None:
    """Uninstall a devkit extension."""
    if package in BUILTIN_PACKAGES:
        print_error(f"{package!r} is a built-in package and cannot be uninstalled")
        raise typer.Exit(1)

    dist_map = packages_distributions()
    installed = {pkg for pkgs in dist_map.values() for pkg in pkgs}
    if package not in installed:
        print_error(f"{package!r} is not currently installed")
        raise typer.Exit(1)

    if not typer.confirm(f"Uninstall {package!r}?"):
        raise typer.Exit(0)

    method = _detect_install_method()

    def _do_uninstall() -> None:
        if method == "pipx":
            result = subprocess.run(
                ["pipx", "uninject", "devkit-cli", package],
                capture_output=True,
                text=True,
            )
        else:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "uninstall", "-y", package],
                capture_output=True,
                text=True,
            )
        if result.returncode != 0:
            print_error(f"Uninstall failed:\n{result.stderr.strip()}")
            raise typer.Exit(2)

    run_with_spinner(_do_uninstall, label=f"Uninstalling {package}...")
    typer.echo(f"Uninstalled {package!r}")


def list_extensions(
    json_: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """List all installed command groups."""
    groups = discover_plugins()
    eps = entry_points(group="devkit.commands")

    ep_by_name: dict[str, Any] = {ep.name: ep for ep in eps}

    rows: list[dict[str, str]] = []
    for group in groups:
        ep = ep_by_name.get(group.name)
        pkg = ep.dist.name if ep and ep.dist else "unknown"
        version = ep.dist.version if ep and ep.dist else "unknown"
        kind = "built-in" if pkg in BUILTIN_PACKAGES else "extension"
        rows.append({"group": group.name, "package": pkg, "version": version, "type": kind})

    if json_:
        typer.echo(json.dumps(rows))
    else:
        print_table(
            ["Group", "Package", "Version", "Type"],
            [(r["group"], r["package"], r["version"], r["type"]) for r in rows],
        )
