from __future__ import annotations

import typer

app = typer.Typer(name="net", help="Network helpers")


class CommandGroup:
    name = "net"
    app = app


# ── net ip ────────────────────────────────────────────────────────────────────

@app.command("ip")
def ip(
    json_: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Show local IPs, public IP, and default gateway."""
    raise NotImplementedError


# ── net port ──────────────────────────────────────────────────────────────────

@app.command("port")
def port(
    number: int = typer.Argument(..., help="Port number (0–65535)"),
    json_: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Show process using <number>."""
    raise NotImplementedError


# ── net serve ─────────────────────────────────────────────────────────────────

@app.command("serve")
def serve(
    port: int = typer.Argument(8000, help="Port to listen on"),
    open_browser: bool = typer.Option(False, "--open", help="Open URL in browser on start"),
) -> None:
    """Start a static HTTP server in the current directory."""
    raise NotImplementedError


# ── net check ─────────────────────────────────────────────────────────────────

@app.command("check")
def check(
    target: str = typer.Argument(..., metavar="host:port", help="TCP target to check"),
    timeout: int = typer.Option(5, "--timeout", help="Connection timeout in seconds"),
    json_: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Check TCP reachability of <host:port>."""
    raise NotImplementedError
