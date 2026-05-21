from __future__ import annotations

from .aliases import ALIASES
from .discovery import discover_plugins

SYSTEM_COMMANDS: frozenset[str] = frozenset({
    "install", "uninstall", "list", "ls", "update", "config",
})


def _zsh_entry(name: str, description: str) -> str:
    safe = description.replace('"', "'").replace(":", "\\:")
    return f'"{name}":"{safe}"'


def grouped_zsh_completions() -> str:
    """Return a zsh _alternative string separating module commands from system commands."""
    plugins = discover_plugins()
    top_level_aliases: dict[str, str] = ALIASES.get("", {})

    module_entries: list[str] = []
    for g in plugins:
        desc = (g.app.info.help or g.name).split("\n")[0]
        module_entries.append(_zsh_entry(g.name, desc))
        for alias, canonical in top_level_aliases.items():
            if canonical == g.name and alias not in SYSTEM_COMMANDS:
                module_entries.append(_zsh_entry(alias, desc))

    system_entries: list[str] = [
        _zsh_entry("install", "Install a devkit extension from PyPI"),
        _zsh_entry("uninstall", "Uninstall a devkit extension"),
        _zsh_entry("list", "List all installed command groups"),
        _zsh_entry("ls", "List all installed command groups"),
        _zsh_entry("update", "Update devkit and its extensions"),
        _zsh_entry("config", "Manage global devkit configuration"),
    ]

    modules_str = " ".join(module_entries)
    system_str = " ".join(system_entries)

    return (
        f"_alternative \\\n"
        f"  'modules:module:(({modules_str}))' \\\n"
        f"  'system:system command:(({system_str}))'"
    )
