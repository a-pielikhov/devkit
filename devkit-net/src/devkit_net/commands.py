from __future__ import annotations

import contextlib
import json
import re
import signal
import socket
import time
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

import psutil
import typer

from devkit_core.output import print_error, print_table
from devkit_core.spinner import run_with_spinner

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

    def _fetch() -> tuple[list[dict[str, str]], str]:
        rows: list[dict[str, str]] = []
        stats = psutil.net_if_stats()
        addrs = psutil.net_if_addrs()

        # Gateway info via netifaces
        gw_by_iface: dict[str, list[str]] = {}
        try:
            import netifaces

            gateways = netifaces.gateways()
            af_inet = netifaces.AF_INET
            for entry in gateways.get(af_inet, []):
                gw_ip, iface, _ = entry
                gw_by_iface.setdefault(iface, []).append(gw_ip)
        except ImportError:
            pass

        for iface, stat in stats.items():
            if not stat.isup:
                continue
            iface_addrs = addrs.get(iface, [])
            local_ips = [a.address for a in iface_addrs if a.family == socket.AF_INET]
            if not local_ips:
                continue
            gw_str = ", ".join(gw_by_iface.get(iface, [])) or "—"
            for local_ip in local_ips:
                rows.append({"interface": iface, "local_ip": local_ip, "gateway": gw_str})

        try:
            with urlopen("https://api.ipify.org", timeout=5) as resp:
                public_ip: str = resp.read().decode().strip()
        except URLError:
            public_ip = "unavailable"

        return rows, public_ip

    rows, public_ip = run_with_spinner(_fetch, label="Fetching network info...")

    if not rows:
        unavailable = {"interface": "unavailable", "local_ip": "unavailable", "gateway": "unavailable"}
        if json_:
            typer.echo(json.dumps([{**unavailable, "public_ip": "unavailable"}]))
        else:
            print_table(
                ["Interface", "Local IP", "Gateway", "Public IP"],
                [("unavailable", "unavailable", "unavailable", "unavailable")],
            )
        return

    if json_:
        result: list[dict[str, Any]] = [
            {**r, "public_ip": public_ip if i == 0 else ""} for i, r in enumerate(rows)
        ]
        typer.echo(json.dumps(result))
    else:
        print_table(
            ["Interface", "Local IP", "Gateway", "Public IP"],
            [
                (r["interface"], r["local_ip"], r["gateway"], public_ip if i == 0 else "—")
                for i, r in enumerate(rows)
            ],
        )


# ── net port ──────────────────────────────────────────────────────────────────


@app.command("port")
def port(
    number: int = typer.Argument(..., help="Port number (0–65535)"),
    json_: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Show process using <number>."""
    if not (0 <= number <= 65535):
        print_error(f"Port {number} is outside valid range 0–65535")
        raise typer.Exit(1)

    connections: list[dict[str, Any]] = []
    try:
        for conn in psutil.net_connections(kind="inet"):
            if conn.laddr and conn.laddr.port == number:
                name = "unknown"
                if conn.pid:
                    with contextlib.suppress(psutil.NoSuchProcess):
                        name = psutil.Process(conn.pid).name()
                proto = "TCP" if conn.type == socket.SOCK_STREAM else "UDP"
                connections.append(
                    {
                        "name": name,
                        "pid": conn.pid,
                        "protocol": proto,
                        "state": conn.status or "—",
                    }
                )
    except psutil.AccessDenied:
        print_error("Permission denied. Run with elevated privileges (sudo / admin) to see all processes.")
        raise typer.Exit(2) from None

    if not connections:
        typer.echo(f"Port {number} is not in use")
        return

    if json_:
        typer.echo(json.dumps(connections))
    else:
        print_table(
            ["Process", "PID", "Protocol", "State"],
            [(c["name"], str(c["pid"]) if c["pid"] else "—", c["protocol"], c["state"]) for c in connections],
        )


# ── net serve ─────────────────────────────────────────────────────────────────


@app.command("serve")
def serve(
    port_num: int = typer.Argument(8000, metavar="port", help="Port to listen on"),
    open_browser: bool = typer.Option(False, "--open", help="Open URL in browser on start"),
) -> None:
    """Start a static HTTP server in the current directory."""
    if not (1 <= port_num <= 65535):
        print_error(f"Port {port_num} is outside valid range 1–65535")
        raise typer.Exit(1)

    try:
        server = HTTPServer(("0.0.0.0", port_num), SimpleHTTPRequestHandler)
    except OSError:
        print_error(f"Port {port_num} is already in use. Try: devkit net serve {port_num + 80}")
        raise typer.Exit(2) from None

    typer.echo(f"Serving http://0.0.0.0:{port_num} — Ctrl+C to stop")

    if open_browser:
        webbrowser.open(f"http://localhost:{port_num}")

    def _handle_sigint(sig: int, frame: object) -> None:
        server.server_close()
        raise SystemExit(0)

    signal.signal(signal.SIGINT, _handle_sigint)
    server.serve_forever()


# ── net check ─────────────────────────────────────────────────────────────────

_IPV6_RE = re.compile(r"^\[(.+)\]:(\d+)$")


@app.command("check")
def check(
    target: str = typer.Argument(..., metavar="host:port", help="TCP target to check"),
    timeout: int = typer.Option(5, "--timeout", help="Connection timeout in seconds"),
    json_: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Check TCP reachability of <host:port>."""
    m = _IPV6_RE.match(target)
    if m:
        host, port_str = m.group(1), m.group(2)
    else:
        parts = target.rsplit(":", 1)
        if len(parts) != 2 or not parts[1]:
            print_error("Invalid format. Use host:port or [ipv6]:port")
            raise typer.Exit(1)
        host, port_str = parts

    try:
        port_num = int(port_str)
    except ValueError:
        print_error(f"Invalid port: {port_str!r}")
        raise typer.Exit(1) from None

    start = time.time()
    try:
        with socket.create_connection((host, port_num), timeout=timeout):
            elapsed = int((time.time() - start) * 1000)
        if json_:
            typer.echo(json.dumps({"status": "open", "host": host, "port": port_num, "response_ms": elapsed}))
        else:
            typer.echo(f"open ({elapsed}ms)")
    except TimeoutError as exc:
        reason = f"timeout after {timeout}s"
        if json_:
            typer.echo(json.dumps({"status": "unreachable", "reason": reason}))
        else:
            typer.echo(f"unreachable ({reason})")
        raise typer.Exit(1) from exc
    except ConnectionRefusedError as exc:
        reason = "connection refused"
        if json_:
            typer.echo(json.dumps({"status": "unreachable", "reason": reason}))
        else:
            typer.echo(f"unreachable ({reason})")
        raise typer.Exit(1) from exc
    except socket.gaierror as exc:
        reason = f"DNS resolution failed: {exc}"
        if json_:
            typer.echo(json.dumps({"status": "unreachable", "reason": reason}))
        else:
            typer.echo(f"unreachable ({reason})")
        raise typer.Exit(1) from exc
    except OSError as exc:
        reason = str(exc)
        if json_:
            typer.echo(json.dumps({"status": "unreachable", "reason": reason}))
        else:
            typer.echo(f"unreachable ({reason})")
        raise typer.Exit(1) from exc
