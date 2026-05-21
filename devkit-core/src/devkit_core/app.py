from __future__ import annotations

import copy

import typer

from .aliases import ALIASES
from .commands import install, list_extensions, uninstall
from .discovery import discover_plugins
from .global_config import app as config_app
from .update_command import app as update_app


def _apply_aliases(root: typer.Typer, sub_apps: dict[str, typer.Typer]) -> None:
    """Register alias names on Typer app instances so they survive get_command() calls."""
    for group_name, group_aliases in ALIASES.items():
        if group_name == "":
            target = root
            source_registered = root.registered_commands
        else:
            sub = sub_apps.get(group_name)
            if sub is None:
                continue
            target = sub
            source_registered = target.registered_commands

        for alias, canonical in group_aliases.items():
            # Find the CommandInfo for the canonical command
            for rc in source_registered:
                if rc.name == canonical:
                    alias_rc = copy.copy(rc)
                    alias_rc.name = alias
                    source_registered.append(alias_rc)
                    break


def build_app() -> typer.Typer:
    app = typer.Typer(
        name="devkit",
        help="Cross-platform developer CLI toolbelt.",
        no_args_is_help=True,
        add_completion=True,
    )

    app.command("install", rich_help_panel="Manage")(install)
    app.command("uninstall", rich_help_panel="Manage")(uninstall)
    app.command("list", rich_help_panel="Manage")(list_extensions)

    sub_apps: dict[str, typer.Typer] = {}
    for group in discover_plugins():
        app.add_typer(group.app, rich_help_panel="Modules")
        sub_apps[group.name] = group.app

    app.add_typer(update_app, rich_help_panel="Manage")
    app.add_typer(config_app, rich_help_panel="Manage")

    _apply_aliases(app, sub_apps)
    return app
