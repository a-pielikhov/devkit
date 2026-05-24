from __future__ import annotations

from .models import CompletionGroup
from .render import describe_call, render_function


def build_top_level_fn(module_group: CompletionGroup, manage_group: CompletionGroup) -> str:
    """Generate _devkit_top_level() with module and manage completions."""
    parts = [
        describe_call(module_group),
        "",
        describe_call(manage_group),
    ]
    return render_function("_devkit_top_level", "\n".join(parts))


def build_group_fn(group_name: str, cmds_group: CompletionGroup) -> str:
    """Generate _devkit_{group_name}() for sub-command completion at depth 3."""
    return render_function(f"_devkit_{group_name}", describe_call(cmds_group))


def build_dispatch_fn(module_names: list[str]) -> str:
    """Generate the main _devkit() dispatcher.

    Routes CURRENT==2 to _devkit_top_level, CURRENT==3 to per-group functions,
    and deeper completions to Typer's native completion engine.
    """
    names_zsh = " ".join(module_names)
    body = "\n".join(
        [
            "  local -a _devkit_mods",
            f"  _devkit_mods=({names_zsh})",
            "  if (( CURRENT == 2 )); then",
            "    _devkit_top_level",
            "  elif (( CURRENT == 3 )) && (( ${_devkit_mods[(I)${words[2]}]} )); then",
            "    _devkit_${words[2]}",
            "  else",
            (
                "    eval $(env"
                ' _TYPER_COMPLETE_ARGS="${words[1,$CURRENT]}"'
                " _DEVKIT_COMPLETE=complete_zsh devkit)"
            ),
            "  fi",
        ]
    )
    return render_function("_devkit", body)


def assemble(
    module_group: CompletionGroup,
    manage_group: CompletionGroup,
    group_fns: list[str],
    dispatch_fn: str,
    extra_groups: list[CompletionGroup] | None = None,
) -> str:
    """Assemble all rendered blocks into a complete zsh compdef script."""
    parts = [
        "#compdef devkit",
        "",
        dispatch_fn,
        "",
        build_top_level_fn(module_group, manage_group),
    ]
    for fn in group_fns:
        parts.extend(["", fn])
    parts.extend(["", '_devkit "$@"', ""])
    return "\n".join(parts)
