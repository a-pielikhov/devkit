from __future__ import annotations

from importlib.metadata import entry_points
from typing import Any, Protocol, runtime_checkable

import typer

from .output import print_error, print_warning


@runtime_checkable
class CommandGroup(Protocol):
    name: str
    app: typer.Typer


def discover_plugins() -> list[Any]:
    eps = entry_points(group="devkit.commands")
    seen: dict[str, str] = {}
    groups = []

    for ep in eps:
        pkg = ep.dist.name if ep.dist else ep.value

        if ep.name in seen:
            print_error(
                f"Entry point conflict: '{ep.name}' registered by both "
                f"{seen[ep.name]} and {pkg}. Uninstall one."
            )
            raise SystemExit(2)
        seen[ep.name] = pkg

        try:
            cls = ep.load()
            group = cls()
            if not (hasattr(group, "name") and hasattr(group, "app")):
                print_warning(
                    f"Plugin '{ep.name}' from {pkg} does not implement the "
                    "CommandGroup protocol (missing 'name' or 'app'). Skipping."
                )
                continue
            groups.append(group)
        except Exception as exc:  # noqa: BLE001
            print_warning(
                f"Failed to load plugin '{ep.name}' from {pkg}: {exc}. Skipping."
            )

    return groups
