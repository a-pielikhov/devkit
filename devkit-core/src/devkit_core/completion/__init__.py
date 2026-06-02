from __future__ import annotations

import os
from pathlib import Path

from ..discovery import discover_plugins  # module-level so patch("...completion.discover_plugins") works
from .sources import SYSTEM_COMMANDS

__all__ = [
    "SYSTEM_COMMANDS",
    "generate_zsh_script",
    "install_zsh_completion",
    "grouped_zsh_completions",
]


def generate_zsh_script() -> str:
    """Orchestrate the completion pipeline and return a complete zsh compdef script."""
    from importlib.metadata import entry_points as _entry_points

    from ..aliases import ALIASES
    from ..commands import BUILTIN_PACKAGES
    from .assemble import assemble, build_dispatch_fn, build_group_fn
    from .sources import command_entries, manage_entries, module_entries

    plugins = discover_plugins()

    eps_map = {ep.name: ep for ep in _entry_points(group="devkit.commands")}
    builtin_names: frozenset[str] = frozenset(
        name for name, ep in eps_map.items() if ep.dist and ep.dist.name in BUILTIN_PACKAGES
    )

    top_aliases = ALIASES.get("", {})
    plugin_names = {g.name for g in plugins}
    module_aliases = {a: c for a, c in top_aliases.items() if c in plugin_names}
    module_group = module_entries(plugins, top_aliases, builtin_names)
    mgmt_group = manage_entries()
    cmd_groups = [command_entries(g) for g in plugins]
    group_fns = [build_group_fn(g.name, cg) for g, cg in zip(plugins, cmd_groups, strict=True)]
    dispatch_fn = build_dispatch_fn([g.name for g in plugins], module_aliases)

    return assemble(module_group, mgmt_group, group_fns, dispatch_fn, extra_groups=cmd_groups)


def install_zsh_completion(target: Path | None = None) -> Path:
    """Write the _devkit zsh completion file and return its path."""
    if target is None:
        zfunc = Path(os.environ.get("ZFUNC_DIR", Path.home() / ".zfunc"))
        target = zfunc / "_devkit"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(generate_zsh_script())
    return target


def grouped_zsh_completions() -> str:
    """Legacy alias for generate_zsh_script()."""
    return generate_zsh_script()
