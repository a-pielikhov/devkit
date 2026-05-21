from __future__ import annotations

import json
from importlib.metadata import EntryPoint
from typing import Any
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from devkit_core.app import build_app

runner = CliRunner()

_app = build_app()


def _make_ep(name: str, dist_name: str = "test-pkg") -> Any:
    ep = MagicMock(spec=EntryPoint)
    ep.name = name
    ep.dist = MagicMock()
    ep.dist.name = dist_name
    ep.dist.version = "1.0.0"
    return ep


# ── devkit list ───────────────────────────────────────────────────────────────


def test_list_shows_groups() -> None:
    group = MagicMock()
    group.name = "git"
    ep = _make_ep("git", "devkit-git")

    with (
        patch("devkit_core.commands.discover_plugins", return_value=[group]),
        patch("devkit_core.commands.entry_points", return_value=[ep]),
    ):
        result = runner.invoke(_app, ["list"])
    assert result.exit_code == 0
    assert "git" in result.output


def test_list_json() -> None:
    group = MagicMock()
    group.name = "git"
    ep = _make_ep("git", "devkit-git")

    with (
        patch("devkit_core.commands.discover_plugins", return_value=[group]),
        patch("devkit_core.commands.entry_points", return_value=[ep]),
    ):
        result = runner.invoke(_app, ["list", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert data[0]["group"] == "git"


def test_list_builtin_type() -> None:
    group = MagicMock()
    group.name = "git"
    ep = _make_ep("git", "devkit-git")

    with (
        patch("devkit_core.commands.discover_plugins", return_value=[group]),
        patch("devkit_core.commands.entry_points", return_value=[ep]),
    ):
        result = runner.invoke(_app, ["list", "--json"])
    data = json.loads(result.output)
    assert data[0]["type"] == "built-in"


def test_list_extension_type() -> None:
    group = MagicMock()
    group.name = "custom"
    ep = _make_ep("custom", "devkit-custom")

    with (
        patch("devkit_core.commands.discover_plugins", return_value=[group]),
        patch("devkit_core.commands.entry_points", return_value=[ep]),
    ):
        result = runner.invoke(_app, ["list", "--json"])
    data = json.loads(result.output)
    assert data[0]["type"] == "extension"


# ── devkit uninstall ──────────────────────────────────────────────────────────


def test_uninstall_builtin_exits_1() -> None:
    result = runner.invoke(_app, ["uninstall", "devkit-git"])
    assert result.exit_code == 1
    assert "built-in" in result.output


def test_uninstall_not_installed_exits_1() -> None:
    with patch("devkit_core.commands.packages_distributions", return_value={}):
        result = runner.invoke(_app, ["uninstall", "devkit-custom"])
    assert result.exit_code == 1
    assert "not currently installed" in result.output


# ── aliases ───────────────────────────────────────────────────────────────────


def test_alias_ls_invokes_list() -> None:
    group = MagicMock()
    group.name = "git"
    ep = _make_ep("git", "devkit-git")

    with (
        patch("devkit_core.commands.discover_plugins", return_value=[group]),
        patch("devkit_core.commands.entry_points", return_value=[ep]),
    ):
        result_ls = runner.invoke(_app, ["ls"])
        result_list = runner.invoke(_app, ["list"])
    assert result_ls.exit_code == result_list.exit_code
    assert result_ls.output == result_list.output
