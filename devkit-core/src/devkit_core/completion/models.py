from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class CompletionEntry:
    name: str
    desc: str


@dataclass(frozen=True)
class CompletionGroup:
    zsh_tag: str
    entries: tuple[CompletionEntry, ...] = ()


class CompletionMeta(Protocol):
    def zsh_arg_completions(self) -> dict[str, str]:
        """Map sub-command name → raw zsh completion function body."""
        ...
