from __future__ import annotations

import typer

from .commands import install, list_extensions, uninstall
from .discovery import discover_plugins


def build_app() -> typer.Typer:
    app = typer.Typer(
        name="devkit",
        help="Cross-platform developer CLI toolbelt.",
        no_args_is_help=True,
        add_completion=False,
    )

    app.command("install")(install)
    app.command("uninstall")(uninstall)
    app.command("list")(list_extensions)

    for group in discover_plugins():
        app.add_typer(group.app)

    return app
