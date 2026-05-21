from __future__ import annotations

import json
from typing import Any

import typer

from .config import ConfigStore
from .output import print_error, print_table  # noqa: F401 — print_table kept for potential future use

# All valid global config keys and their defaults
_GLOBAL_KEYS: dict[str, dict[str, Any]] = {
    "update": {
        "auto_check_enabled": True,
        "auto_check_interval_days": 7,
    },
}

app = typer.Typer(name="config", help="Manage global devkit configuration.", no_args_is_help=True)
_store = ConfigStore()


def _resolve_key(dotted: str) -> tuple[str, str]:
    """Split 'section.key' into (section, key). Exits 1 if invalid."""
    parts = dotted.split(".", 1)
    if len(parts) != 2:
        print_error(f"Key must be in 'section.key' format, got: {dotted!r}")
        raise typer.Exit(1)
    section, key = parts
    if section not in _GLOBAL_KEYS or key not in _GLOBAL_KEYS[section]:
        valid = [f"{s}.{k}" for s, keys in _GLOBAL_KEYS.items() for k in keys]
        print_error(f"Unknown config key {dotted!r}. Valid keys: {', '.join(valid)}")
        raise typer.Exit(1)
    return section, key


@app.command("set")
def config_set(
    key: str = typer.Argument(..., help="Config key in section.key format"),
    value: str = typer.Argument(..., help="Value to set"),
) -> None:
    """Set a global config value."""
    section, k = _resolve_key(key)
    default = _GLOBAL_KEYS[section][k]
    # coerce value to match the default type
    if isinstance(default, bool):
        coerced: Any = value.lower() in ("true", "1", "yes")
    elif isinstance(default, int):
        try:
            coerced = int(value)
        except ValueError:
            print_error(f"Expected an integer for {key!r}, got {value!r}")
            raise typer.Exit(1) from None
    else:
        coerced = value
    _store.add(section, k, coerced, replace=True)
    typer.echo(f"Set {key} = {coerced}")


@app.command("get")
def config_get(
    key: str = typer.Argument(..., help="Config key in section.key format"),
) -> None:
    """Get a global config value."""
    section, k = _resolve_key(key)
    default = _GLOBAL_KEYS[section][k]
    value = _store.get(section, k, default=default)
    typer.echo(str(value))


@app.command("show")
def config_show(
    json_: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Show all global config values."""
    result: dict[str, Any] = {}
    for section, keys in _GLOBAL_KEYS.items():
        result[section] = {k: _store.get(section, k, default=v) for k, v in keys.items()}
    if json_:
        typer.echo(json.dumps(result))
    else:
        for section, keys in result.items():
            typer.echo(f"[{section}]")
            for k, v in keys.items():
                typer.echo(f"  {k} = {v}")


@app.command("reset")
def config_reset(
    key: str = typer.Argument(..., help="Config key in section.key format"),
) -> None:
    """Reset a global config value to its default."""
    section, k = _resolve_key(key)
    _store.remove(section, k)
    default = _GLOBAL_KEYS[section][k]
    typer.echo(f"Reset {key} to default ({default})")
