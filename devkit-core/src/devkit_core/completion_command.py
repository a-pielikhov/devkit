from __future__ import annotations

from pathlib import Path

import typer

app = typer.Typer(name="completion", help="Manage zsh tab completion.")


@app.command("regenerate")
def regenerate(
    target: Path | None = typer.Option(None, "--target", help="Override output path"),
) -> None:
    """Regenerate the _devkit zsh completion file (~/.zfunc/_devkit)."""
    from .completion import install_zsh_completion
    path = install_zsh_completion(target)
    typer.echo(f"Completion written to {path}")
