from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

from devkit_core.updater import (
    maybe_notify_update,
)

# ── maybe_notify_update ───────────────────────────────────────────────────────


def test_maybe_notify_update_disabled_prints_nothing(tmp_path: Path, capsys: Any) -> None:
    with patch("devkit_core.updater._CACHE_PATH", tmp_path / "update-cache.json"):
        maybe_notify_update(enabled=False, interval_days=7, current_version="0.1.0")
    captured = capsys.readouterr()
    assert captured.out == ""


def test_maybe_notify_update_prints_notice_when_newer_known(tmp_path: Path, capsys: Any) -> None:
    cache_path = tmp_path / "update-cache.json"
    # Write a fresh cache (recent check, so no new thread spawned) with a newer version
    recent = datetime.now(tz=UTC).isoformat()
    cache_path.write_text(json.dumps({"last_check_timestamp": recent, "latest_known_version": "0.2.0"}))
    with patch("devkit_core.updater._CACHE_PATH", cache_path):
        maybe_notify_update(enabled=True, interval_days=7, current_version="0.1.0")
    captured = capsys.readouterr()
    assert "Update available" in captured.out
    assert "0.2.0" in captured.out


def test_maybe_notify_update_no_notice_when_up_to_date(tmp_path: Path, capsys: Any) -> None:
    cache_path = tmp_path / "update-cache.json"
    recent = datetime.now(tz=UTC).isoformat()
    cache_path.write_text(json.dumps({"last_check_timestamp": recent, "latest_known_version": "0.1.0"}))
    with patch("devkit_core.updater._CACHE_PATH", cache_path):
        maybe_notify_update(enabled=True, interval_days=7, current_version="0.1.0")
    captured = capsys.readouterr()
    assert "Update available" not in captured.out


def test_maybe_notify_update_fresh_cache_does_not_spawn_thread(tmp_path: Path) -> None:
    cache_path = tmp_path / "update-cache.json"
    recent = datetime.now(tz=UTC).isoformat()
    cache_path.write_text(json.dumps({"last_check_timestamp": recent, "latest_known_version": "0.1.0"}))
    with patch("devkit_core.updater._CACHE_PATH", cache_path):
        maybe_notify_update(enabled=True, interval_days=7, current_version="0.1.0")
    # Daemon threads may vary; the key assertion is that no new non-daemon thread was started
    # We verify by checking that _background_check was NOT called by patching it
    called = []

    def fake_background_check(interval_days: int) -> None:
        called.append(True)

    with (
        patch("devkit_core.updater._background_check", fake_background_check),
        patch("devkit_core.updater._CACHE_PATH", cache_path),
    ):
        maybe_notify_update(enabled=True, interval_days=7, current_version="0.1.0")
    assert called == [], "Background check should not be spawned when cache is fresh"


def test_maybe_notify_update_stale_cache_spawns_check(tmp_path: Path) -> None:
    cache_path = tmp_path / "update-cache.json"
    old_time = (datetime.now(tz=UTC) - timedelta(days=10)).isoformat()
    cache_path.write_text(json.dumps({"last_check_timestamp": old_time, "latest_known_version": "0.1.0"}))
    called = []

    def fake_background_check(interval_days: int) -> None:
        called.append(True)

    with (
        patch("devkit_core.updater._background_check", fake_background_check),
        patch("devkit_core.updater._CACHE_PATH", cache_path),
        patch("threading.Thread") as mock_thread,
    ):
        mock_thread.return_value = MagicMock()
        maybe_notify_update(enabled=True, interval_days=7, current_version="0.1.0")
        assert mock_thread.called, "Expected a background thread to be spawned for stale cache"


# ── _cmd_check shape ──────────────────────────────────────────────────────────


def test_cmd_check_returns_correct_shape(tmp_path: Path) -> None:
    from devkit_core.update_command import _cmd_check

    mock_packages = [{"package": "devkit-core", "version": "0.1.0"}]
    with (
        patch("devkit_core.update_command.get_installed_packages", return_value=mock_packages),
        patch("devkit_core.update_command._fetch_latest_version", return_value="0.2.0"),
    ):
        # Capture output via typer echo — invoke through CliRunner
        import typer
        from typer.testing import CliRunner

        test_app = typer.Typer()

        @test_app.command()
        def _inner(json_: bool = typer.Option(False, "--json")) -> None:
            _cmd_check(json_=json_)

        result = CliRunner().invoke(test_app, ["--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        row = data[0]
        assert "package" in row
        assert "current" in row
        assert "latest" in row
        assert "status" in row


# ── _cmd_list shape ───────────────────────────────────────────────────────────


def test_cmd_list_returns_rows_from_api(tmp_path: Path) -> None:
    from devkit_core.update_command import _cmd_list

    mock_releases = [
        {"tag_name": "v0.2.0", "published_at": "2026-01-01T00:00:00Z", "name": "Release v0.2.0", "assets": []}
    ]
    with patch("devkit_core.update_command._fetch_all_releases", return_value=mock_releases):
        import typer
        from typer.testing import CliRunner

        test_app = typer.Typer()

        @test_app.command()
        def _inner(json_: bool = typer.Option(False, "--json")) -> None:
            _cmd_list(json_=json_)

        result = CliRunner().invoke(test_app, ["--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 1
        assert data[0]["tag"] == "v0.2.0"
        assert data[0]["date"] == "2026-01-01"
