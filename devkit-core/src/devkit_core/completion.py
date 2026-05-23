from __future__ import annotations

import os
from pathlib import Path

from .aliases import ALIASES
from .discovery import discover_plugins

SYSTEM_COMMANDS: frozenset[str] = frozenset({
    "install", "uninstall", "list", "ls", "update", "config",
})

_MANAGE_ENTRIES = [
    "install:Install a devkit extension from PyPI",
    "uninstall:Uninstall a devkit extension",
    "list:List all installed command groups",
    "ls:List all installed command groups",
    "update:Update devkit and its extensions",
    "config:Manage global devkit configuration",
]

# Variant-3 ANSI palette (cyan modules / amber manage)
_MOD_ESC  = r"\e[38;2;79;195;247m"
_MGMT_ESC = r"\e[38;2;255;183;77m"
_RST_ESC  = r"\e[0m"

_ZSH_TEMPLATE = """\
#compdef devkit

_devkit() {{
  if (( CURRENT == 2 )); then
    _devkit_top_level
  else
    eval $(env _TYPER_COMPLETE_ARGS="${{words[1,$CURRENT]}}" _DEVKIT_COMPLETE=complete_zsh devkit)
  fi
}}

_devkit_top_level() {{
  zstyle ':completion:*:devkit-modules:*' format $'{mod_esc}── Modules ──{rst_esc}'
  zstyle ':completion:*:devkit-manage:*'  format $'{mgmt_esc}── Manage ──{rst_esc}'

  local -a module_cmds manage_cmds
  module_cmds=(
{modules}
  )
  manage_cmds=(
{manage}
  )

  _describe -t devkit-modules '' module_cmds
  _describe -t devkit-manage  '' manage_cmds
}}

_devkit "$@"
"""


def _zsh_entry(name: str, description: str) -> str:
    safe = description.replace('"', "'").replace(":", "\\:")
    return f'"{name}:{safe}"'


def generate_zsh_script() -> str:
    """Return a complete _devkit zsh compdef script with Variant-3 colors."""
    plugins = discover_plugins()
    top_level_aliases: dict[str, str] = ALIASES.get("", {})

    module_lines: list[str] = []
    for g in plugins:
        desc = (g.app.info.help or g.name).split("\n")[0]
        module_lines.append(f"    {_zsh_entry(g.name, desc)}")
        for alias, canonical in top_level_aliases.items():
            if canonical == g.name and alias not in SYSTEM_COMMANDS:
                module_lines.append(f"    {_zsh_entry(alias, desc)}")

    manage_lines = [f"    {_zsh_entry(*e.split(':', 1))}" for e in _MANAGE_ENTRIES]

    return _ZSH_TEMPLATE.format(
        mod_esc=_MOD_ESC,
        mgmt_esc=_MGMT_ESC,
        rst_esc=_RST_ESC,
        modules="\n".join(module_lines),
        manage="\n".join(manage_lines),
    )


def install_zsh_completion(target: Path | None = None) -> Path:
    """Write the _devkit zsh completion file and return its path."""
    if target is None:
        zfunc = Path(os.environ.get("ZFUNC_DIR", Path.home() / ".zfunc"))
        target = zfunc / "_devkit"

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(generate_zsh_script())
    return target


# Legacy helper kept for any callers that imported it
def grouped_zsh_completions() -> str:
    return generate_zsh_script()
