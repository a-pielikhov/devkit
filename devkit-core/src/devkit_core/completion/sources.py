from __future__ import annotations

from typing import Any

from .models import CompletionEntry, CompletionGroup

SYSTEM_COMMANDS: frozenset[str] = frozenset(
    {
        "install",
        "uninstall",
        "list",
        "ls",
        "update",
        "config",
    }
)

_MANAGE_DATA: list[tuple[str, str]] = [
    ("install", "Install a devkit extension from PyPI"),
    ("uninstall", "Uninstall a devkit extension"),
    ("list", "List all installed command groups"),
    ("ls", "List all installed command groups"),
    ("update", "Update devkit and its extensions"),
    ("config", "Manage global devkit configuration"),
]


def module_entries(
    plugins: list[Any],
    top_level_aliases: dict[str, str],
    builtin_names: frozenset[str],
) -> CompletionGroup:
    """Build CompletionGroup for top-level module completions."""
    entries: list[CompletionEntry] = []
    for g in plugins:
        desc = (g.app.info.help or g.name).split("\n")[0]
        entries.append(CompletionEntry(name=g.name, desc=desc))
        for alias, canonical in top_level_aliases.items():
            if canonical == g.name and alias not in SYSTEM_COMMANDS:
                entries.append(CompletionEntry(name=alias, desc=desc))
    return CompletionGroup(zsh_tag="devkit-modules", entries=tuple(entries))


def manage_entries() -> CompletionGroup:
    """Build CompletionGroup for top-level manage command completions."""
    entries = [CompletionEntry(name=name, desc=desc) for name, desc in _MANAGE_DATA]
    return CompletionGroup(zsh_tag="devkit-manage", entries=tuple(entries))


def command_entries(group: Any) -> CompletionGroup:
    """Build CompletionGroup for a module's sub-commands via Typer/Click introspection."""
    entries: list[CompletionEntry] = []
    try:
        import click
        import typer.main as _typer_main

        click_group = _typer_main.get_command(group.app)
        if not isinstance(click_group, click.Group):
            return CompletionGroup(zsh_tag=f"devkit-{group.name}-cmds", entries=())
        for name, click_cmd in click_group.commands.items():
            desc = (click_cmd.help or "").split("\n")[0]
            entries.append(CompletionEntry(name=name, desc=desc))
    except Exception:
        pass
    return CompletionGroup(zsh_tag=f"devkit-{group.name}-cmds", entries=tuple(entries))
