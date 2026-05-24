from __future__ import annotations

from unittest.mock import MagicMock, patch

from devkit_core.completion import (
    SYSTEM_COMMANDS,
    _zsh_entry,
    generate_zsh_script,
    grouped_zsh_completions,
)


def _make_plugin(name: str, help_text: str) -> MagicMock:
    g = MagicMock()
    g.name = name
    g.app.info.help = help_text
    return g


def test_zsh_entry_formats_colon_separated() -> None:
    assert _zsh_entry("cmd", "A description") == '"cmd:A description"'


def test_zsh_entry_escapes_colon_in_description() -> None:
    assert _zsh_entry("cmd", "Desc: with colon") == '"cmd:Desc\\: with colon"'


def test_zsh_entry_escapes_double_quotes() -> None:
    assert _zsh_entry("cmd", 'Say "hi"') == "\"cmd:Say 'hi'\""


def test_system_commands_set() -> None:
    assert "install" in SYSTEM_COMMANDS
    assert "ls" in SYSTEM_COMMANDS
    assert "git" not in SYSTEM_COMMANDS


def test_generate_zsh_script_structure() -> None:
    plugins = [_make_plugin("git", "Git helpers")]
    with patch("devkit_core.completion.discover_plugins", return_value=plugins):
        result = generate_zsh_script()
    assert "#compdef devkit" in result
    assert "_devkit_top_level" in result
    assert "_DEVKIT_COMPLETE=complete_zsh" in result


def test_generate_zsh_script_has_colored_group_headers() -> None:
    plugins = [_make_plugin("git", "Git helpers")]
    with patch("devkit_core.completion.discover_plugins", return_value=plugins):
        result = generate_zsh_script()
    # Both group headers use dim gray (#707070 = rgb 112,112,112)
    assert "38;2;112;112;112" in result
    assert "Modules" in result
    assert "Manage" in result


def test_generate_zsh_script_modules_and_manage_are_separate() -> None:
    plugins = [_make_plugin("git", "Git helpers"), _make_plugin("net", "Network helpers")]
    with patch("devkit_core.completion.discover_plugins", return_value=plugins):
        result = generate_zsh_script()

    modules_array = result.split("_devkit_modules=(\n")[1].split("\n  )")[0]
    manage_array = result.split("_devkit_manage=(\n")[1].split("\n  )")[0]

    assert "git" in modules_array
    assert "net" in modules_array
    assert "install" in manage_array
    assert "config" in manage_array
    assert "git" not in manage_array


def test_generate_zsh_script_module_aliases_in_modules() -> None:
    plugins = [
        _make_plugin("encode", "Encoding and conversion"),
        _make_plugin("decode", "Decoding and conversion"),
    ]
    with patch("devkit_core.completion.discover_plugins", return_value=plugins):
        result = generate_zsh_script()

    modules_array = result.split("_devkit_modules=(\n")[1].split("\n  )")[0]
    assert "enc" in modules_array
    assert "dec" in modules_array


def test_generate_zsh_script_ls_in_manage() -> None:
    plugins = [_make_plugin("git", "Git helpers")]
    with patch("devkit_core.completion.discover_plugins", return_value=plugins):
        result = generate_zsh_script()

    manage_array = result.split("_devkit_manage=(\n")[1].split("\n  )")[0]
    assert "ls" in manage_array


def test_grouped_zsh_completions_is_alias_for_generate() -> None:
    plugins = [_make_plugin("git", "Git helpers")]
    with patch("devkit_core.completion.discover_plugins", return_value=plugins):
        assert grouped_zsh_completions() == generate_zsh_script()
