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
    # _zsh_entry now produces "name:desc" format (zsh _describe style)
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
    # Cyan modules header
    assert "38;2;79;195;247" in result
    # Amber manage header
    assert "38;2;255;183;77" in result
    assert "Modules" in result
    assert "Manage" in result


def test_generate_zsh_script_modules_and_manage_are_separate() -> None:
    plugins = [_make_plugin("git", "Git helpers"), _make_plugin("net", "Network helpers")]
    with patch("devkit_core.completion.discover_plugins", return_value=plugins):
        result = generate_zsh_script()

    # manage_cmds=( appears once, after module_cmds=(...)
    modules_section = result.split("manage_cmds=(")[0]
    manage_section = result.split("manage_cmds=(")[1]

    assert "git" in modules_section
    assert "net" in modules_section
    assert "install" in manage_section
    assert "config" in manage_section
    assert "git" not in manage_section


def test_generate_zsh_script_module_aliases_in_modules() -> None:
    plugins = [
        _make_plugin("encode", "Encoding and conversion"),
        _make_plugin("decode", "Decoding and conversion"),
    ]
    with patch("devkit_core.completion.discover_plugins", return_value=plugins):
        result = generate_zsh_script()

    modules_section = result.split("manage_cmds=(")[0]
    assert "enc" in modules_section
    assert "dec" in modules_section


def test_generate_zsh_script_ls_in_manage() -> None:
    plugins = [_make_plugin("git", "Git helpers")]
    with patch("devkit_core.completion.discover_plugins", return_value=plugins):
        result = generate_zsh_script()

    manage_section = result.split("manage_cmds=(")[1]
    assert "ls" in manage_section


def test_grouped_zsh_completions_is_alias_for_generate() -> None:
    # grouped_zsh_completions() should return the same script as generate_zsh_script()
    plugins = [_make_plugin("git", "Git helpers")]
    with patch("devkit_core.completion.discover_plugins", return_value=plugins):
        assert grouped_zsh_completions() == generate_zsh_script()
