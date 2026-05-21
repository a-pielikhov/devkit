from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from devkit_core.app import build_app
from devkit_core.config import ConfigStore
from devkit_core.updater import maybe_notify_update

app = build_app()

_store = ConfigStore()


def main() -> None:
    try:
        current_version = version("devkit-core")
    except PackageNotFoundError:
        current_version = "0.0.0"

    enabled: bool = _store.get("update", "auto_check_enabled", default=True)
    interval_days: int = _store.get("update", "auto_check_interval_days", default=7)

    maybe_notify_update(
        enabled=bool(enabled),
        interval_days=int(interval_days),
        current_version=current_version,
    )

    app()
