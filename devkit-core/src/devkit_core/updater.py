from __future__ import annotations

import json
import threading
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

from .commands import BUILTIN_PACKAGES, _detect_install_method  # noqa: F401
from .config import _CONFIG_PATH

_CACHE_PATH = _CONFIG_PATH.parent / "update-cache.json"
_GITHUB_API = "https://api.github.com/repos/artempielikhov/devkit/releases"
_REQUEST_TIMEOUT = 5  # seconds


def _read_cache() -> dict[str, Any]:
    if not _CACHE_PATH.exists():
        return {}
    try:
        return json.loads(_CACHE_PATH.read_text())  # type: ignore[no-any-return]
    except (json.JSONDecodeError, OSError):
        return {}


def _write_cache(data: dict[str, Any]) -> None:
    _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CACHE_PATH.write_text(json.dumps(data))


def _fetch_latest_version() -> str | None:
    """Query GitHub Releases API for the latest version tag. Returns None on error."""
    try:
        with urlopen(f"{_GITHUB_API}/latest", timeout=_REQUEST_TIMEOUT) as resp:
            data = json.loads(resp.read())
            return data.get("tag_name")  # type: ignore[no-any-return]
    except (URLError, json.JSONDecodeError, KeyError, OSError):
        return None


def _fetch_all_releases() -> list[dict[str, Any]]:
    """Return list of releases from GitHub API."""
    try:
        with urlopen(_GITHUB_API, timeout=_REQUEST_TIMEOUT) as resp:
            return json.loads(resp.read())  # type: ignore[no-any-return]
    except (URLError, json.JSONDecodeError, OSError):
        return []


def _background_check(interval_days: int) -> None:
    """Run update check in background thread and write result to cache."""
    latest = _fetch_latest_version()
    if latest:
        _write_cache(
            {
                "last_check_timestamp": datetime.now(tz=UTC).isoformat(),
                "latest_known_version": latest,
            }
        )


def maybe_notify_update(enabled: bool, interval_days: int, current_version: str) -> None:
    """Called on every devkit invocation. Spawns background check if due; prints notice if update known."""
    if not enabled:
        return
    cache = _read_cache()
    last_check_str = cache.get("last_check_timestamp")
    latest_known = cache.get("latest_known_version")

    # Spawn background check if interval has elapsed or never run
    due = True
    if last_check_str:
        try:
            last_check = datetime.fromisoformat(last_check_str)
            due = datetime.now(tz=UTC) - last_check > timedelta(days=interval_days)
        except ValueError:
            due = True
    if due:
        t = threading.Thread(target=_background_check, args=(interval_days,), daemon=True)
        t.start()

    # Print notice if a newer version is known
    if latest_known and latest_known != current_version:
        print(f"\n  Update available: {latest_known} → run `devkit update` to install")


def get_installed_packages() -> list[dict[str, str]]:
    """Return list of installed devkit-* packages with current versions."""
    from importlib.metadata import entry_points

    eps = entry_points(group="devkit.commands")
    seen: set[str] = set()
    result = []
    for ep in eps:
        if ep.dist and ep.dist.name not in seen:
            seen.add(ep.dist.name)
            result.append({"package": ep.dist.name, "version": ep.dist.version})
    return result
