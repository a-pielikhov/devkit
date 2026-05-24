from __future__ import annotations

from typing import Any

from .models import CompletionEntry, CompletionGroup

SYSTEM_COMMANDS: frozenset[str] = frozenset({
    "install", "uninstall", "list", "ls", "update", "config",
})

_MANAGE_DATA: list[tuple[str, str]] = [
    ("install",   "Install a devkit extension from PyPI"),
    ("uninstall", "Uninstall a devkit extension"),
    ("list",      "List all installed command groups"),
    ("ls",        "List all installed command groups"),
    ("update",    "Update devkit and its extensions"),
    ("config",    "Manage global devkit configuration"),
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
        is_builtin = g.name in builtin_names
        tag = "built-in" if is_builtin else "extension"
        tag_color = "#708090" if is_builtin else "#ffd700"
        entries.append(CompletionEntry(
            name=g.name,
            desc=desc,
            tag=tag,
            name_color="#dc143c",
            tag_color=tag_color,
        ))
        for alias, canonical in top_level_aliases.items():
            if canonical == g.name and alias not in SYSTEM_COMMANDS:
                entries.append(CompletionEntry(
                    name=alias,
                    desc=desc,
                    tag=tag,
                    name_color="#dc143c",
                    tag_color=tag_color,
                ))
    return CompletionGroup(
        zsh_tag="devkit-modules",
        heading="── Modules ──",
        entries=tuple(entries),
        heading_color="#707070",
        name_bold=True,
    )


def manage_entries() -> CompletionGroup:
    """Build CompletionGroup for top-level manage command completions."""
    entries = [
        CompletionEntry(name=name, desc=desc, tag="", name_color="#e0e0e0", tag_color="#708090")
        for name, desc in _MANAGE_DATA
    ]
    return CompletionGroup(
        zsh_tag="devkit-manage",
        heading="── Manage ──",
        entries=tuple(entries),
        heading_color="#707070",
        name_bold=False,
    )


def command_entries(group: Any) -> CompletionGroup:
    """Build CompletionGroup for a module's sub-commands via Typer/Click introspection."""
    entries: list[CompletionEntry] = []
    try:
        import click
        import typer.main as _typer_main
        click_group = _typer_main.get_command(group.app)
        if not isinstance(click_group, click.Group):
            return CompletionGroup(
                zsh_tag=f"devkit-{group.name}-cmds",
                heading=f"── {group.name} commands ──",
                entries=(),
                heading_color="#707070",
                name_bold=True,
            )
        for name, click_cmd in click_group.commands.items():
            desc = (click_cmd.help or "").split("\n")[0]
            tag, tag_color = _infer_tag(click_cmd)
            entries.append(CompletionEntry(
                name=name,
                desc=desc,
                tag=tag,
                name_color="#dc143c",
                tag_color=tag_color,
            ))
    except Exception:
        pass
    return CompletionGroup(
        zsh_tag=f"devkit-{group.name}-cmds",
        heading=f"── {group.name} commands ──",
        entries=tuple(entries),
        heading_color="#707070",
        name_bold=True,
    )


def _infer_tag(cmd: Any) -> tuple[str, str]:
    """Return (tag_text, tag_color) from the command's most prominent parameter."""
    import click
    if not hasattr(cmd, "params"):
        return "", "#708090"
    for p in cmd.params:
        if isinstance(p, click.Argument):
            return f"<{p.human_readable_name.lower()}>", "#708090"   # steel
    for p in cmd.params:
        if isinstance(p, click.Option) and p.opts and not p.is_eager:
            return p.opts[0], "#ffd700"   # gold
    return "", "#708090"
