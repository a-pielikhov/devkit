from __future__ import annotations

from .models import CompletionEntry, CompletionGroup

# Color constants come from devkit_core.output.STYLES — matched by hex value here
# to avoid importing Rich-dependent modules from this pure renderer.


def _rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _ansi_esc(hex_color: str, bold: bool = False) -> str:
    """Return a zsh $'...'-literal ANSI 24-bit escape sequence (uses \\e notation)."""
    r, g, b = _rgb(hex_color)
    prefix = "1;" if bold else ""
    return f"\\e[{prefix}38;2;{r};{g};{b}m"


def _rst() -> str:
    return "\\e[0m"


def zsh_entry(entry: CompletionEntry) -> str:
    """Return a _describe-compatible "name:safe_desc" quoted string."""
    safe = entry.desc.replace('"', "'").replace(":", "\\:")
    return f'"{entry.name}:{safe}"'


def zstyle_format(group: CompletionGroup) -> str:
    """Return a zstyle ':completion:*:TAG:*' format line for the group's section header."""
    esc = _ansi_esc(group.heading_color)
    rst = _rst()
    return f"  zstyle ':completion:*:{group.zsh_tag}:*' format $'{esc}{group.heading}{rst}'"


def zstyle_listcolors(group: CompletionGroup) -> str:
    """Return a zstyle list-colors line to uniformly color all entry names in this group."""
    if not group.entries:
        return ""
    r, g, b = _rgb(group.entries[0].name_color)
    bold_prefix = "1;" if group.name_bold else ""
    return f"  zstyle ':completion:*:{group.zsh_tag}:*' list-colors 'no={bold_prefix}38;2;{r};{g};{b}'"


def describe_call(group: CompletionGroup) -> str:
    """Return zsh: local -a array; array=(...); _describe -t TAG '' array."""
    var = f"_{group.zsh_tag.replace('-', '_')}"
    lines = [f"  local -a {var}", f"  {var}=("]
    for entry in group.entries:
        lines.append(f"    {zsh_entry(entry)}")
    lines.append("  )")
    lines.append(f"  _describe -t {group.zsh_tag} '' {var}")
    return "\n".join(lines)


def render_function(name: str, body: str) -> str:
    """Return a complete zsh function definition."""
    return f"{name}() {{\n{body}\n}}"
