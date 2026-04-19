from __future__ import annotations

import contextlib
import os
import tempfile
import tomllib
from pathlib import Path
from typing import Any

import tomli_w

from .output import print_error

_CONFIG_PATH = Path.home() / ".config" / "devkit" / "config.toml"


class ConfigStore:
    def __init__(self, path: Path = _CONFIG_PATH) -> None:
        self._path = path

    def _load(self) -> dict[str, Any]:
        if not self._path.exists():
            return {}
        try:
            with open(self._path, "rb") as f:
                return tomllib.load(f)
        except tomllib.TOMLDecodeError as exc:
            print_error(f"Config file is malformed: {exc}. Fix or delete {self._path}")
            raise SystemExit(2) from exc

    def _save(self, data: dict[str, Any]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=self._path.parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "wb") as f:
                tomli_w.dump(data, f)
            os.replace(tmp_path, self._path)
        except Exception:
            with contextlib.suppress(OSError):
                os.unlink(tmp_path)
            raise

    def get(self, module: str, key: str, default: Any = None) -> Any:
        return self._load().get(module, {}).get(key, default)

    def add(self, module: str, key: str, value: Any, *, replace: bool = False) -> None:
        data = self._load()
        section = data.setdefault(module, {})
        if replace or key not in section:
            section[key] = value
            self._save(data)
            return
        existing = section[key]
        if isinstance(existing, list):
            if value not in existing:
                existing.append(value)
        elif existing != value:
            section[key] = [existing, value]
        self._save(data)

    def remove(self, module: str, key: str, value: Any | None = None) -> None:
        data = self._load()
        section = data.get(module, {})
        if key not in section:
            return
        if value is None:
            del section[key]
        else:
            existing = section[key]
            if isinstance(existing, list):
                if value in existing:
                    existing.remove(value)
                if len(existing) == 1:
                    section[key] = existing[0]
                elif not existing:
                    del section[key]
            elif existing == value:
                del section[key]
        if not section:
            data.pop(module, None)
        self._save(data)

    def remove_all(self, module: str) -> None:
        data = self._load()
        data.pop(module, None)
        self._save(data)

    def show(self, module: str) -> dict[str, Any]:
        result = self._load().get(module, {})
        return dict(result)
