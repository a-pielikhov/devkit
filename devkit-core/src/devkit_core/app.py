from __future__ import annotations

import copy
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as pkg_version
from typing import Any

import typer
import typer.rich_utils as _ru
from rich.console import Console
from rich.text import Text

from .aliases import ALIASES
from .banner import print_banner
from .commands import install, list_extensions, uninstall
from .discovery import discover_plugins
from .global_config import app as config_app
from .term import is_decorative_ok
from .update_command import app as update_app

# ── Help-screen styling ───────────────────────────────────────────────────────
_ru.STYLE_OPTIONS_PANEL_BORDER = "#a50f2d"        # 75% crimson on black
_ru.STYLE_COMMANDS_PANEL_BORDER = "#3e464f"       # steel dim
_ru.OPTIONS_PANEL_TITLE = "[bold #dc143c]Options"
_ru.STYLE_OPTION = "#ffd700"                      # flag names gold
_ru.STYLE_SWITCH = "#ffd700"
_ru.STYLE_OPTION_HELP = "#9d9d9d"                 # option help ink
_ru.STYLE_HELPTEXT = "#9d9d9d"                    # command help text ink
_ru.STYLE_HELPTEXT_FIRST_LINE = "#9d9d9d"
_ru.STYLE_USAGE = "bold #e0e0e0"                  # "Usage:" bold moon
_ru.STYLE_USAGE_COMMAND = "#e0e0e0"               # command in usage moon
_ru.STYLE_COMMANDS_TABLE_FIRST_COLUMN = "bold #dc143c"  # command names bold crimson

_MODULES_PANEL = "[bold #ffd700]Modules"
_MANAGE_PANEL = "[bold #708090]Manage"


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
            for rc in source_registered:
                if rc.name == canonical:
                    alias_rc = copy.copy(rc)
                    alias_rc.name = alias
                    source_registered.append(alias_rc)
                    break


def _print_boot_screen(version: str, groups: list[Any]) -> None:
    """Custom first-run screen shown when `devkit` is invoked with no arguments."""
    console = Console()

    # dim2 = rgba(224,224,224,0.32) — ultra-quiet horizontal rule
    sep = Text("  " + "─" * 64, style="#474747")
    console.print(sep)
    console.print()

    module_names = [g.name for g in groups]
    manage_commands = ["install", "uninstall", "list", "update", "config"]

    if is_decorative_ok():
        # .dim label (50% moon), .grp module names (crimson bold), 3 spaces between
        mod_label = Text("  Modules   ", style="#707070")
        for i, name in enumerate(module_names):
            mod_label.append(name, style="bold #dc143c")
            if i < len(module_names) - 1:
                mod_label.append("   ")
        console.print(mod_label)

        # .dim label, .ink commands (70% moon), 2 spaces between
        mgmt_label = Text("  Manage    ", style="#707070")
        for i, cmd in enumerate(manage_commands):
            mgmt_label.append(cmd, style="#9d9d9d")
            if i < len(manage_commands) - 1:
                mgmt_label.append("  ")
        console.print(mgmt_label)
    else:
        console.print(f"  Modules   {'   '.join(module_names)}")
        console.print(f"  Manage    {'  '.join(manage_commands)}")

    console.print()
    # .ink for static text, bold .moon for command names
    hint = Text("  Try ", style="#9d9d9d")
    hint.append("devkit --help", style="bold #e0e0e0")
    hint.append(" or ", style="#9d9d9d")
    hint.append("devkit list", style="bold #e0e0e0")
    hint.append(" to get started.", style="#9d9d9d")
    console.print(hint)
    console.print()


def build_app() -> typer.Typer:
    app = typer.Typer(
        name="devkit",
        help="Cross-platform developer CLI toolbelt.",
        no_args_is_help=False,
        add_completion=True,
    )

    @app.callback(invoke_without_command=True)
    def _root(
        ctx: typer.Context,
        _version: bool = typer.Option(False, "--version", help="Show version and exit."),
    ) -> None:
        if _version:
            try:
                ver = pkg_version("devkit-core")
            except PackageNotFoundError:
                ver = "0.0.0"
            typer.echo(f"v{ver}")
            raise typer.Exit()
        if ctx.invoked_subcommand is None:
            try:
                ver = pkg_version("devkit-core")
            except PackageNotFoundError:
                ver = "0.0.0"
            groups = discover_plugins()
            print_banner(ver)
            _print_boot_screen(ver, groups)
            raise typer.Exit()

    app.command("install", rich_help_panel=_MANAGE_PANEL)(install)
    app.command("uninstall", rich_help_panel=_MANAGE_PANEL)(uninstall)
    app.command("list", rich_help_panel=_MANAGE_PANEL)(list_extensions)

    sub_apps: dict[str, typer.Typer] = {}
    for group in discover_plugins():
        app.add_typer(group.app, rich_help_panel=_MODULES_PANEL)
        sub_apps[group.name] = group.app

    app.add_typer(update_app, rich_help_panel=_MANAGE_PANEL)
    app.add_typer(config_app, rich_help_panel=_MANAGE_PANEL)

    _apply_aliases(app, sub_apps)
    return app
