from __future__ import annotations

import json
import socket
from typing import Any
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from devkit_net.commands import app

runner = CliRunner()


# ── net port ──────────────────────────────────────────────────────────────────


def test_port_out_of_range_exits_1() -> None:
    result = runner.invoke(app, ["port", "99999"])
    assert result.exit_code == 1


def test_port_not_in_use(monkeypatch: Any) -> None:
    with patch("devkit_net.commands.psutil.net_connections", return_value=[]):
        result = runner.invoke(app, ["port", "9999"])
    assert result.exit_code == 0
    assert "not in use" in result.output


def test_port_shows_process(monkeypatch: Any) -> None:
    conn = MagicMock()
    conn.laddr.port = 8080
    conn.pid = 1234
    conn.type = socket.SOCK_STREAM
    conn.status = "LISTEN"
    proc = MagicMock()
    proc.name.return_value = "nginx"

    with (
        patch("devkit_net.commands.psutil.net_connections", return_value=[conn]),
        patch("devkit_net.commands.psutil.Process", return_value=proc),
    ):
        result = runner.invoke(app, ["port", "8080"])
    assert result.exit_code == 0
    assert "nginx" in result.output


def test_port_json(monkeypatch: Any) -> None:
    conn = MagicMock()
    conn.laddr.port = 8080
    conn.pid = 1234
    conn.type = socket.SOCK_STREAM
    conn.status = "LISTEN"
    proc = MagicMock()
    proc.name.return_value = "nginx"

    with (
        patch("devkit_net.commands.psutil.net_connections", return_value=[conn]),
        patch("devkit_net.commands.psutil.Process", return_value=proc),
    ):
        result = runner.invoke(app, ["port", "8080", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert data[0]["name"] == "nginx"


# ── net check ─────────────────────────────────────────────────────────────────


def test_check_open(monkeypatch: Any) -> None:
    mock_conn = MagicMock()
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)

    with patch("devkit_net.commands.socket.create_connection", return_value=mock_conn):
        result = runner.invoke(app, ["check", "localhost:9999"])
    assert result.exit_code == 0
    assert "open" in result.output


def test_check_connection_refused(monkeypatch: Any) -> None:
    with patch("devkit_net.commands.socket.create_connection", side_effect=ConnectionRefusedError):
        result = runner.invoke(app, ["check", "localhost:9999"])
    assert result.exit_code == 1
    assert "unreachable" in result.output
    assert "connection refused" in result.output


def test_check_timeout(monkeypatch: Any) -> None:
    with patch("devkit_net.commands.socket.create_connection", side_effect=TimeoutError):
        result = runner.invoke(app, ["check", "localhost:9999"])
    assert result.exit_code == 1
    assert "unreachable" in result.output
    assert "timeout" in result.output


def test_check_invalid_format_exits_1() -> None:
    result = runner.invoke(app, ["check", "nocolon"])
    assert result.exit_code == 1


def test_check_json_open(monkeypatch: Any) -> None:
    mock_conn = MagicMock()
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)

    with patch("devkit_net.commands.socket.create_connection", return_value=mock_conn):
        result = runner.invoke(app, ["check", "localhost:9999", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["status"] == "open"


def test_check_json_unreachable(monkeypatch: Any) -> None:
    with patch("devkit_net.commands.socket.create_connection", side_effect=ConnectionRefusedError):
        result = runner.invoke(app, ["check", "localhost:9999", "--json"])
    assert result.exit_code == 1
    data = json.loads(result.output)
    assert data["status"] == "unreachable"


def test_check_ipv6_bracket_notation(monkeypatch: Any) -> None:
    mock_conn = MagicMock()
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)

    with patch("devkit_net.commands.socket.create_connection", return_value=mock_conn) as mock_create:
        result = runner.invoke(app, ["check", "[::1]:8080"])
    assert result.exit_code == 0
    mock_create.assert_called_once_with(("::1", 8080), timeout=5)


# ── net ip ────────────────────────────────────────────────────────────────────


def test_ip_unavailable_when_no_interfaces(monkeypatch: Any) -> None:
    with (
        patch("devkit_net.commands.psutil.net_if_stats", return_value={}),
        patch("devkit_net.commands.psutil.net_if_addrs", return_value={}),
    ):
        result = runner.invoke(app, ["ip"])
    assert result.exit_code == 0
    assert "unavailable" in result.output


def test_ip_public_unavailable_on_error(monkeypatch: Any) -> None:
    from urllib.error import URLError

    stat = MagicMock()
    stat.isup = True
    addr = MagicMock()
    addr.family = socket.AF_INET
    addr.address = "192.168.1.100"

    with (
        patch("devkit_net.commands.psutil.net_if_stats", return_value={"eth0": stat}),
        patch("devkit_net.commands.psutil.net_if_addrs", return_value={"eth0": [addr]}),
        patch("devkit_net.commands.urlopen", side_effect=URLError("timeout")),
    ):
        result = runner.invoke(app, ["ip"])
    assert result.exit_code == 0
    assert "unavailable" in result.output
