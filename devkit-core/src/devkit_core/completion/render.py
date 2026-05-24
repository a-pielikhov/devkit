from __future__ import annotations

from .models import CompletionGroup


def _zsh_single_quote(s: str) -> str:
    return "'" + s.replace("'", "'\\''") + "'"


def describe_call(group: CompletionGroup) -> str:
    """Return zsh: compadd -l -d display_arr -- name_arr.

    -l forces one-per-line list display so descriptions appear inline with names.
    -d provides display strings of the form 'name  -- description'.
    """
    var = f"_{group.zsh_tag.replace('-', '_')}"
    disp = f"{var}_d"
    lines = [f"  local -a {var} {disp}", f"  {var}=("]
    for entry in group.entries:
        lines.append(f"    {_zsh_single_quote(entry.name)}")
    lines.append("  )")
    lines.append(f"  {disp}=(")
    for entry in group.entries:
        display = f"{entry.name}  -- {entry.desc}"
        lines.append(f"    {_zsh_single_quote(display)}")
    lines.append("  )")
    lines.append(f"  compadd -l -d {disp} -- ${var}")
    return "\n".join(lines)


def render_function(name: str, body: str) -> str:
    """Return a complete zsh function definition."""
    return f"{name}() {{\n{body}\n}}"
