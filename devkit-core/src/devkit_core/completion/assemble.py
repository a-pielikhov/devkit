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


def build_dispatch_fn(
    module_names: list[str],
    module_aliases: dict[str, str] | None = None,
) -> str:
    """Generate the main _devkit() dispatcher.

    Routes CURRENT==2 to _devkit_top_level, CURRENT==3 to per-group functions,
    and deeper completions to Typer's native completion engine.

    module_aliases maps alias → canonical for top-level group aliases only
    (e.g. {"enc": "encode", "dec": "decode"}). Aliases for non-group commands
    (e.g. ls → list) must be omitted — they have no per-group function.
    """
    known = set(module_names)
    aliases = {a: c for a, c in (module_aliases or {}).items() if c in known}
    all_mods = list(module_names) + sorted(aliases)
    names_zsh = " ".join(all_mods)

    parts: list[str] = [
        "  local -a _devkit_mods",
        f"  _devkit_mods=({names_zsh})",
    ]

    if aliases:
        parts.append("  local _canon=${words[2]}")
        parts.append("  case ${words[2]} in")
        for alias, canonical in sorted(aliases.items()):
            parts.append(f"    {alias}) _canon={canonical} ;;")
        parts.append("  esac")
        group_ref = "    _devkit_${_canon}"
    else:
        group_ref = "    _devkit_${words[2]}"

    # Build the Typer fallback args expression. When module aliases are present
    # (e.g. dec→decode), words[2] may be the alias which Typer doesn't know —
    # so reconstruct the args with the resolved canonical name instead.
    typer_args = '"${words[1]} ${_canon} ${(j: :)words[3,$CURRENT]}"' if aliases else '"${words[1,$CURRENT]}"'

    parts += [
        "  if (( CURRENT == 2 )); then",
        "    _devkit_top_level",
        "  elif (( CURRENT == 3 )) && (( ${_devkit_mods[(I)${words[2]}]} )); then",
        group_ref,
        "  else",
        f"    eval $(env _TYPER_COMPLETE_ARGS={typer_args} _DEVKIT_COMPLETE=complete_zsh devkit)",
        "  fi",
    ]
    body = "\n".join(parts)
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
