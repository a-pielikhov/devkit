from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class CompletionEntry:
    name: str
    desc: str
    tag: str = ""
    name_color: str = "#e0e0e0"    # moon
    tag_color: str = "#708090"     # steel


@dataclass(frozen=True)
class CompletionGroup:
    zsh_tag: str
    heading: str = ""
    entries: tuple[CompletionEntry, ...] = ()
    heading_color: str = "#707070"  # dim
    name_bold: bool = False


class CompletionMeta(Protocol):
    def zsh_arg_completions(self) -> dict[str, str]:
        """Map sub-command name → raw zsh completion function body."""
        ...
