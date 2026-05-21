from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.request import urlretrieve

import typer

from .commands import BUILTIN_PACKAGES
from .output import print_error, print_table
from .spinner import run_with_spinner
from .updater import _fetch_all_releases, _fetch_latest_version, get_installed_packages

app = typer.Typer(
    name="update",
    help="Update devkit and its extensions.",
    no_args_is_help=False,
    invoke_without_command=True,
)


@app.callback(invoke_without_command=True)
def update(
    ctx: typer.Context,
    package: str = typer.Argument(None, help="Specific extension package to update"),
    check: bool = typer.Option(False, "--check", help="Print version table without installing"),
    list_: bool = typer.Option(False, "--list", help="List all available releases"),
    version: str = typer.Option(None, "--version", help="Install a specific release tag"),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n", help="Show what would be installed without installing"
    ),
    json_: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Update devkit and installed extensions."""
    if ctx.invoked_subcommand is not None:
        return

    if list_:
        _cmd_list(json_=json_)
        return
    if check:
        _cmd_check(json_=json_)
        return
    if version:
        _cmd_install_version(version, dry_run=dry_run)
        return
    _cmd_upgrade_all(package=package, dry_run=dry_run)


def _cmd_list(json_: bool) -> None:
    releases = _fetch_all_releases()
    if not releases:
        typer.echo("Could not reach GitHub API")
        raise typer.Exit(1)
    rows = [
        {"tag": r["tag_name"], "date": r["published_at"][:10], "title": r.get("name") or r["tag_name"]}
        for r in releases
    ]
    if json_:
        typer.echo(json.dumps(rows))
    else:
        print_table(["Tag", "Date", "Title"], [(r["tag"], r["date"], r["title"]) for r in rows])


def _cmd_check(json_: bool) -> None:
    installed = get_installed_packages()
    latest_tag = _fetch_latest_version()
    rows = []
    for pkg in installed:
        if pkg["package"] in BUILTIN_PACKAGES or pkg["package"] == "devkit-cli":
            latest = latest_tag or "unknown"
            up_to_date = (latest == pkg["version"]) if latest != "unknown" else True
        else:
            latest = "PyPI"  # extensions checked via PyPI separately
            up_to_date = True
        rows.append(
            {
                "package": pkg["package"],
                "current": pkg["version"],
                "latest": latest,
                "status": "up to date" if up_to_date else "update available",
            }
        )
    if json_:
        typer.echo(json.dumps(rows))
    else:
        print_table(
            ["Package", "Current", "Latest", "Status"],
            [(r["package"], r["current"], r["latest"], r["status"]) for r in rows],
        )


def _cmd_install_version(tag: str, dry_run: bool) -> None:
    releases = _fetch_all_releases()
    release = next((r for r in releases if r["tag_name"] == tag), None)
    if not release:
        print_error(f"Release {tag!r} not found on GitHub")
        raise typer.Exit(2)
    if dry_run:
        typer.echo(f"Would install {tag}")
        return
    _install_from_release(release)


def _cmd_upgrade_all(package: str | None, dry_run: bool) -> None:
    if package:
        # Single extension via pipx inject --upgrade
        if dry_run:
            typer.echo(f"Would upgrade {package}")
            return
        _upgrade_extension(package)
        return

    latest_tag = _fetch_latest_version()
    if not latest_tag:
        print_error("Could not reach GitHub API")
        raise typer.Exit(1)

    if dry_run:
        typer.echo(f"Would install {latest_tag} (main bundle) and upgrade all extensions")
        return

    if not typer.confirm(f"Install {latest_tag} and upgrade all extensions?"):
        raise typer.Exit(0)

    releases = _fetch_all_releases()
    release = next((r for r in releases if r["tag_name"] == latest_tag), None)
    if release:
        _install_from_release(release)

    # Upgrade user-installed extensions
    installed = get_installed_packages()
    for pkg in installed:
        if pkg["package"] not in BUILTIN_PACKAGES and pkg["package"] != "devkit-cli":
            _upgrade_extension(pkg["package"])


def _install_from_release(release: dict[str, object]) -> None:
    """Download wheel from GitHub Release and install via pipx."""
    python_tag = f"cp{sys.version_info.major}{sys.version_info.minor}"
    assets = release.get("assets", [])
    if not isinstance(assets, list):
        assets = []
    wheel = next(
        (
            a
            for a in assets
            if isinstance(a, dict) and a.get("name", "").endswith(".whl") and python_tag in a.get("name", "")
        ),
        next((a for a in assets if isinstance(a, dict) and a.get("name", "").endswith(".whl")), None),
    )
    if not wheel or not isinstance(wheel, dict):
        print_error("No wheel found in this release")
        raise typer.Exit(1)

    wheel_name = wheel["name"]
    download_url = wheel["browser_download_url"]

    with tempfile.TemporaryDirectory() as tmpdir:
        dest = Path(tmpdir) / wheel_name

        def _download() -> None:
            urlretrieve(download_url, dest)

        run_with_spinner(_download, label=f"Downloading {wheel_name}...")

        def _install() -> None:
            result = subprocess.run(
                ["pipx", "install", "--find-links", tmpdir, "devkit-cli", "--force"],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                print_error(f"Install failed:\n{result.stderr.strip()}")
                raise typer.Exit(2)

        run_with_spinner(_install, label="Installing...")
    typer.echo(f"Installed {release['tag_name']}")


def _upgrade_extension(package: str) -> None:
    def _do() -> None:
        result = subprocess.run(
            ["pipx", "inject", "devkit-cli", package, "--pip-args=--upgrade"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print_error(f"Failed to upgrade {package}:\n{result.stderr.strip()}")

    run_with_spinner(_do, label=f"Upgrading {package}...")
    typer.echo(f"Upgraded {package}")
