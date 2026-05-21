from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

from typer.testing import CliRunner

from devkit_core.app import build_app

runner = CliRunner()


def _app_with_tmp_home(tmp_path: Path) -> Any:
    """Build the app with HOME pointing at tmp_path so ConfigStore uses a temp file."""
    return build_app()


# ── devkit config set / get / show / reset ────────────────────────────────────


def test_config_set_and_get(tmp_path: Path) -> None:
    app = build_app()
    with patch.dict("os.environ", {"HOME": str(tmp_path)}):
        result = runner.invoke(app, ["config", "set", "update.auto_check_enabled", "false"])
        assert result.exit_code == 0, result.output
        result = runner.invoke(app, ["config", "get", "update.auto_check_enabled"])
        assert result.exit_code == 0
        assert "False" in result.output


def test_config_get_default(tmp_path: Path) -> None:
    app = build_app()
    with patch.dict("os.environ", {"HOME": str(tmp_path)}):
        result = runner.invoke(app, ["config", "get", "update.auto_check_interval_days"])
        assert result.exit_code == 0
        assert "7" in result.output


def test_config_show_prints_all_keys(tmp_path: Path) -> None:
    app = build_app()
    with patch.dict("os.environ", {"HOME": str(tmp_path)}):
        result = runner.invoke(app, ["config", "show"])
        assert result.exit_code == 0
        assert "auto_check_enabled" in result.output
        assert "auto_check_interval_days" in result.output


def test_config_show_json(tmp_path: Path) -> None:
    app = build_app()
    with patch.dict("os.environ", {"HOME": str(tmp_path)}):
        result = runner.invoke(app, ["config", "show", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "update" in data
        assert "auto_check_enabled" in data["update"]
        assert "auto_check_interval_days" in data["update"]


def test_config_reset_restores_default(tmp_path: Path) -> None:
    app = build_app()
    with patch.dict("os.environ", {"HOME": str(tmp_path)}):
        runner.invoke(app, ["config", "set", "update.auto_check_enabled", "false"])
        result = runner.invoke(app, ["config", "reset", "update.auto_check_enabled"])
        assert result.exit_code == 0
        result = runner.invoke(app, ["config", "get", "update.auto_check_enabled"])
        assert "True" in result.output


def test_config_set_unknown_key_exits_1(tmp_path: Path) -> None:
    app = build_app()
    with patch.dict("os.environ", {"HOME": str(tmp_path)}):
        result = runner.invoke(app, ["config", "set", "nonexistent.key", "value"])
        assert result.exit_code == 1


def test_config_get_unknown_key_exits_1(tmp_path: Path) -> None:
    app = build_app()
    with patch.dict("os.environ", {"HOME": str(tmp_path)}):
        result = runner.invoke(app, ["config", "get", "bad.key"])
        assert result.exit_code == 1


def test_config_key_missing_dot_exits_1(tmp_path: Path) -> None:
    app = build_app()
    with patch.dict("os.environ", {"HOME": str(tmp_path)}):
        result = runner.invoke(app, ["config", "set", "nodot", "value"])
        assert result.exit_code == 1
