from __future__ import annotations

from pathlib import Path

import pytest

from devkit_core.config import ConfigStore


def test_get_returns_none_when_no_config(tmp_path: Path) -> None:
    store = ConfigStore(tmp_path / "config.toml")
    assert store.get("git", "protected_branches") is None


def test_get_returns_default_when_missing(tmp_path: Path) -> None:
    store = ConfigStore(tmp_path / "config.toml")
    assert store.get("git", "protected_branches", default=["main"]) == ["main"]


def test_add_creates_key(tmp_path: Path) -> None:
    store = ConfigStore(tmp_path / "config.toml")
    store.add("git", "protected_branches", "main")
    assert store.get("git", "protected_branches") == "main"


def test_add_appends_second_value_as_list(tmp_path: Path) -> None:
    store = ConfigStore(tmp_path / "config.toml")
    store.add("git", "protected_branches", "main")
    store.add("git", "protected_branches", "develop")
    assert store.get("git", "protected_branches") == ["main", "develop"]


def test_add_does_not_duplicate_existing_value(tmp_path: Path) -> None:
    store = ConfigStore(tmp_path / "config.toml")
    store.add("git", "protected_branches", "main")
    store.add("git", "protected_branches", "main")
    assert store.get("git", "protected_branches") == "main"


def test_add_replace_overwrites(tmp_path: Path) -> None:
    store = ConfigStore(tmp_path / "config.toml")
    store.add("git", "protected_branches", "main")
    store.add("git", "protected_branches", "develop")
    store.add("git", "protected_branches", "trunk", replace=True)
    assert store.get("git", "protected_branches") == "trunk"


def test_add_multiple_modules_isolated(tmp_path: Path) -> None:
    store = ConfigStore(tmp_path / "config.toml")
    store.add("git", "protected_branches", "main")
    store.add("net", "timeout", "30")
    assert store.get("git", "protected_branches") == "main"
    assert store.get("net", "timeout") == "30"


def test_remove_specific_value_from_list(tmp_path: Path) -> None:
    store = ConfigStore(tmp_path / "config.toml")
    store.add("git", "protected_branches", "main")
    store.add("git", "protected_branches", "develop")
    store.remove("git", "protected_branches", "develop")
    assert store.get("git", "protected_branches") == "main"


def test_remove_last_value_deletes_key(tmp_path: Path) -> None:
    store = ConfigStore(tmp_path / "config.toml")
    store.add("git", "protected_branches", "main")
    store.remove("git", "protected_branches", "main")
    assert store.get("git", "protected_branches") is None


def test_remove_entire_key(tmp_path: Path) -> None:
    store = ConfigStore(tmp_path / "config.toml")
    store.add("git", "protected_branches", "main")
    store.remove("git", "protected_branches")
    assert store.get("git", "protected_branches") is None


def test_remove_missing_key_is_silent(tmp_path: Path) -> None:
    store = ConfigStore(tmp_path / "config.toml")
    store.remove("git", "nonexistent_key")


def test_remove_missing_value_is_silent(tmp_path: Path) -> None:
    store = ConfigStore(tmp_path / "config.toml")
    store.add("git", "protected_branches", "main")
    store.remove("git", "protected_branches", "does-not-exist")
    assert store.get("git", "protected_branches") == "main"


def test_remove_all_clears_module(tmp_path: Path) -> None:
    store = ConfigStore(tmp_path / "config.toml")
    store.add("git", "protected_branches", "main")
    store.add("git", "default_branch", "main")
    store.remove_all("git")
    assert store.show("git") == {}


def test_remove_all_leaves_other_modules(tmp_path: Path) -> None:
    store = ConfigStore(tmp_path / "config.toml")
    store.add("git", "protected_branches", "main")
    store.add("net", "timeout", "30")
    store.remove_all("git")
    assert store.get("net", "timeout") == "30"


def test_show_returns_module_dict(tmp_path: Path) -> None:
    store = ConfigStore(tmp_path / "config.toml")
    store.add("git", "protected_branches", "main")
    store.add("git", "default_branch", "main")
    result = store.show("git")
    assert "protected_branches" in result
    assert "default_branch" in result


def test_show_returns_empty_dict_when_missing(tmp_path: Path) -> None:
    store = ConfigStore(tmp_path / "config.toml")
    assert store.show("git") == {}


def test_malformed_toml_exits_2(tmp_path: Path) -> None:
    config_file = tmp_path / "config.toml"
    config_file.write_text("this is not [valid toml !!!")
    store = ConfigStore(config_file)
    with pytest.raises(SystemExit) as exc_info:
        store.get("git", "anything")
    assert exc_info.value.code == 2
