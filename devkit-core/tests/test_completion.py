from __future__ import annotations

from unittest.mock import MagicMock, patch

from devkit_core.completion import SYSTEM_COMMANDS, _zsh_entry, grouped_zsh_completions


def _make_plugin(name: str, help_text: str) -> MagicMock:
    g = MagicMock()
    g.name = name
    g.app.info.help = help_text
    return g


def test_zsh_entry_escapes_colon() -> None:
    assert _zsh_entry("cmd", "Desc: with colon") == '"cmd":"Desc\\: with colon"'


def test_zsh_entry_escapes_double_quotes() -> None:
    assert _zsh_entry("cmd", 'Say "hi"') == "\"cmd\":\"Say 'hi'\""


def test_system_commands_set() -> None:
    assert "install" in SYSTEM_COMMANDS
    assert "ls" in SYSTEM_COMMANDS
    assert "git" not in SYSTEM_COMMANDS


def test_grouped_zsh_output_has_alternative() -> None:
    plugins = [_make_plugin("git", "Git helpers")]
    with patch("devkit_core.completion.discover_plugins", return_value=plugins):
        result = grouped_zsh_completions()
    assert "_alternative" in result
    assert "modules:module" in result
    assert "system:system command" in result


def test_grouped_zsh_modules_and_system_are_separate() -> None:
    plugins = [_make_plugin("git", "Git helpers"), _make_plugin("net", "Network helpers")]
    with patch("devkit_core.completion.discover_plugins", return_value=plugins):
        result = grouped_zsh_completions()

    modules_section = result.split("'system:")[0]
    system_section = result.split("'system:")[1]

    assert '"git"' in modules_section
    assert '"net"' in modules_section
    assert '"install"' in system_section
    assert '"config"' in system_section
    assert '"git"' not in system_section


def test_grouped_zsh_module_aliases_in_modules_section() -> None:
    plugins = [
        _make_plugin("encode", "Encoding and conversion"),
        _make_plugin("decode", "Decoding and conversion"),
    ]
    with patch("devkit_core.completion.discover_plugins", return_value=plugins):
        result = grouped_zsh_completions()

    modules_section = result.split("'system:")[0]
    assert '"enc"' in modules_section
    assert '"dec"' in modules_section


def test_grouped_zsh_ls_alias_in_system_section() -> None:
    plugins = [_make_plugin("git", "Git helpers")]
    with patch("devkit_core.completion.discover_plugins", return_value=plugins):
        result = grouped_zsh_completions()

    system_section = result.split("'system:")[1]
    assert '"ls"' in system_section
