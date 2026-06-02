from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from devkit_core.completion import (
    SYSTEM_COMMANDS,
    generate_zsh_script,
    grouped_zsh_completions,
    install_zsh_completion,
)
from devkit_core.completion.assemble import build_dispatch_fn, build_group_fn
from devkit_core.completion.models import CompletionEntry, CompletionGroup
from devkit_core.completion.render import describe_call, render_function
from devkit_core.completion.sources import manage_entries, module_entries


def _make_plugin(name: str, help_text: str) -> MagicMock:
    g = MagicMock()
    g.name = name
    g.app.info.help = help_text
    return g


# ── public API ────────────────────────────────────────────────────────────────


def test_system_commands_set() -> None:
    assert "install" in SYSTEM_COMMANDS
    assert "ls" in SYSTEM_COMMANDS
    assert "git" not in SYSTEM_COMMANDS


# ── generate_zsh_script ───────────────────────────────────────────────────────


def test_generate_zsh_script_structure() -> None:
    plugins = [_make_plugin("git", "Git helpers")]
    with patch("devkit_core.completion.discover_plugins", return_value=plugins):
        result = generate_zsh_script()
    assert "#compdef devkit" in result
    assert "_devkit_top_level" in result
    assert "_DEVKIT_COMPLETE=complete_zsh" in result


def test_generate_zsh_script_no_color_sequences() -> None:
    plugins = [_make_plugin("git", "Git helpers")]
    with patch("devkit_core.completion.discover_plugins", return_value=plugins):
        result = generate_zsh_script()
    assert "38;2;" not in result
    assert "%F{" not in result
    assert "list-colors" not in result


def test_generate_zsh_script_uses_compadd() -> None:
    plugins = [_make_plugin("git", "Git helpers")]
    with patch("devkit_core.completion.discover_plugins", return_value=plugins):
        result = generate_zsh_script()
    assert "compadd -l -d" in result


def test_generate_zsh_script_modules_with_inline_descriptions() -> None:
    plugins = [_make_plugin("git", "Branch hygiene")]
    with patch("devkit_core.completion.discover_plugins", return_value=plugins):
        result = generate_zsh_script()
    assert "git  -- Branch hygiene" in result


def test_generate_zsh_script_modules_and_manage_present() -> None:
    plugins = [_make_plugin("git", "Git helpers"), _make_plugin("net", "Network helpers")]
    with patch("devkit_core.completion.discover_plugins", return_value=plugins):
        result = generate_zsh_script()
    assert "git" in result
    assert "net" in result
    assert "install" in result
    assert "config" in result


def test_generate_zsh_script_module_aliases_present() -> None:
    plugins = [
        _make_plugin("encode", "Encoding and conversion"),
        _make_plugin("decode", "Decoding and conversion"),
    ]
    with patch("devkit_core.completion.discover_plugins", return_value=plugins):
        result = generate_zsh_script()
    assert "enc  -- Encoding and conversion" in result
    assert "dec  -- Decoding and conversion" in result


def test_generate_zsh_script_ls_in_manage() -> None:
    plugins = [_make_plugin("git", "Git helpers")]
    with patch("devkit_core.completion.discover_plugins", return_value=plugins):
        result = generate_zsh_script()
    assert "ls  -- List all installed command groups" in result


def test_grouped_zsh_completions_is_alias_for_generate() -> None:
    plugins = [_make_plugin("git", "Git helpers")]
    with patch("devkit_core.completion.discover_plugins", return_value=plugins):
        assert grouped_zsh_completions() == generate_zsh_script()


# ── render.describe_call ──────────────────────────────────────────────────────


def test_describe_call_uses_compadd() -> None:
    entry = CompletionEntry(name="cmd", desc="do something")
    group = CompletionGroup(zsh_tag="test-cmds", entries=(entry,))
    result = describe_call(group)
    assert "compadd -l -d" in result


def test_describe_call_name_in_names_array() -> None:
    entry = CompletionEntry(name="uuid", desc="Generate UUID")
    group = CompletionGroup(zsh_tag="test-cmds", entries=(entry,))
    result = describe_call(group)
    lines = result.splitlines()
    names_section = "\n".join(lines)
    assert "'uuid'" in names_section


def test_describe_call_inline_display_string() -> None:
    entry = CompletionEntry(name="uuid", desc="Generate UUID")
    group = CompletionGroup(zsh_tag="test-cmds", entries=(entry,))
    result = describe_call(group)
    assert "uuid  -- Generate UUID" in result


def test_describe_call_declares_two_arrays() -> None:
    entry = CompletionEntry(name="x", desc="y")
    group = CompletionGroup(zsh_tag="my-tag", entries=(entry,))
    result = describe_call(group)
    assert "local -a _my_tag _my_tag_d" in result


def test_describe_call_escapes_single_quote_in_desc() -> None:
    entry = CompletionEntry(name="cmd", desc="don't panic")
    group = CompletionGroup(zsh_tag="test-cmds", entries=(entry,))
    result = describe_call(group)
    assert "don'\\''t panic" in result


# ── render.render_function ────────────────────────────────────────────────────


def test_render_function_wraps_body() -> None:
    result = render_function("_devkit_test", "  echo hi")
    assert result == "_devkit_test() {\n  echo hi\n}"


# ── assemble.build_dispatch_fn ────────────────────────────────────────────────


def test_build_dispatch_fn_routes_current_2() -> None:
    result = build_dispatch_fn(["git", "net"])
    assert "CURRENT == 2" in result
    assert "_devkit_top_level" in result


def test_build_dispatch_fn_routes_current_3() -> None:
    result = build_dispatch_fn(["git", "net"])
    assert "CURRENT == 3" in result
    assert "_devkit_${words[2]}" in result


def test_build_dispatch_fn_module_aliases_in_mods_array() -> None:
    result = build_dispatch_fn(["encode", "decode"], {"enc": "encode", "dec": "decode"})
    assert "enc" in result
    assert "dec" in result
    assert "encode" in result
    assert "decode" in result


def test_build_dispatch_fn_alias_case_statement() -> None:
    result = build_dispatch_fn(["encode", "decode"], {"enc": "encode", "dec": "decode"})
    assert "dec) _canon=decode" in result
    assert "enc) _canon=encode" in result


def test_build_dispatch_fn_alias_uses_canon_variable() -> None:
    result = build_dispatch_fn(["encode"], {"enc": "encode"})
    assert "_devkit_${_canon}" in result
    assert "local _canon=${words[2]}" in result


def test_build_dispatch_fn_alias_typer_fallback_uses_canon() -> None:
    # When aliases are present the Typer fallback must pass the canonical name
    # so that Typer (which doesn't know about aliases) receives e.g. "decode"
    # not "dec" — otherwise it falls back to top-level completions.
    result = build_dispatch_fn(["encode", "decode"], {"enc": "encode", "dec": "decode"})
    assert "${words[1]} ${_canon} ${(j: :)words[3,$CURRENT]}" in result


def test_build_dispatch_fn_no_alias_typer_fallback_uses_words() -> None:
    # Without aliases the original words slice is used unchanged.
    result = build_dispatch_fn(["git"])
    assert "${words[1,$CURRENT]}" in result


def test_build_dispatch_fn_non_module_alias_excluded() -> None:
    # "ls" maps to "list" which is not in module_names — no alias resolution generated
    result = build_dispatch_fn(["git"], {"ls": "list"})
    assert "_canon" not in result
    assert "_devkit_mods=(git)" in result


def test_generate_zsh_script_alias_dispatch() -> None:
    plugins = [
        _make_plugin("encode", "Encoding and conversion"),
        _make_plugin("decode", "Decoding and conversion"),
    ]
    with patch("devkit_core.completion.discover_plugins", return_value=plugins):
        result = generate_zsh_script()
    assert "enc" in result
    assert "dec) _canon=decode" in result
    assert "enc) _canon=encode" in result
    assert "_devkit_${_canon}" in result


def test_build_dispatch_fn_has_typer_fallback() -> None:
    result = build_dispatch_fn(["git"])
    assert "_DEVKIT_COMPLETE=complete_zsh" in result


def test_build_dispatch_fn_lists_module_names() -> None:
    result = build_dispatch_fn(["git", "net", "file"])
    assert "git net file" in result


# ── assemble.build_group_fn ───────────────────────────────────────────────────


def test_build_group_fn_generates_named_function() -> None:
    entry = CompletionEntry(name="clean-branches", desc="Delete branches")
    group = CompletionGroup(zsh_tag="devkit-git-cmds", entries=(entry,))
    result = build_group_fn("git", group)
    assert "_devkit_git() {" in result
    assert "compadd -l -d" in result


def test_build_group_fn_includes_inline_description() -> None:
    entry = CompletionEntry(name="uuid", desc="Generate UUID")
    group = CompletionGroup(zsh_tag="devkit-encode-cmds", entries=(entry,))
    result = build_group_fn("encode", group)
    assert "uuid  -- Generate UUID" in result


# ── sources.module_entries ────────────────────────────────────────────────────


def test_module_entries_tag_is_devkit_modules() -> None:
    plugin = _make_plugin("git", "Git helpers")
    result = module_entries([plugin], {}, frozenset())
    assert result.zsh_tag == "devkit-modules"


def test_module_entries_includes_plugin_name_and_desc() -> None:
    plugin = _make_plugin("git", "Git helpers")
    result = module_entries([plugin], {}, frozenset())
    entry = next(e for e in result.entries if e.name == "git")
    assert entry.desc == "Git helpers"


def test_module_entries_aliases_included() -> None:
    plugin = _make_plugin("encode", "Encoding")
    result = module_entries([plugin], {"enc": "encode"}, frozenset())
    names = [e.name for e in result.entries]
    assert "encode" in names
    assert "enc" in names


def test_module_entries_system_aliases_excluded() -> None:
    plugin = _make_plugin("list", "List commands")
    result = module_entries([plugin], {"ls": "list"}, frozenset())
    names = [e.name for e in result.entries]
    assert "ls" not in names


# ── sources.manage_entries ────────────────────────────────────────────────────


def test_manage_entries_tag_is_devkit_manage() -> None:
    result = manage_entries()
    assert result.zsh_tag == "devkit-manage"


def test_manage_entries_has_all_commands() -> None:
    result = manage_entries()
    names = {e.name for e in result.entries}
    assert {"install", "uninstall", "list", "ls", "update", "config"} <= names


# ── install_zsh_completion ────────────────────────────────────────────────────


def test_install_zsh_completion_writes_file(tmp_path: Path) -> None:
    target = tmp_path / "_devkit"
    plugins = [_make_plugin("git", "Git helpers")]
    with patch("devkit_core.completion.discover_plugins", return_value=plugins):
        returned = install_zsh_completion(target)
    assert returned == target
    assert target.exists()
    assert "#compdef devkit" in target.read_text()


def test_install_zsh_completion_creates_parent_dirs(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "dir" / "_devkit"
    plugins = [_make_plugin("git", "Git helpers")]
    with patch("devkit_core.completion.discover_plugins", return_value=plugins):
        install_zsh_completion(target)
    assert target.exists()


# ── completion regenerate CLI ─────────────────────────────────────────────────


def test_completion_regenerate_command_writes_file(tmp_path: Path) -> None:
    from devkit_core.app import build_app

    app = build_app()
    runner = CliRunner()
    target = tmp_path / "_devkit"
    plugins = [_make_plugin("git", "Git helpers")]
    with patch("devkit_core.completion.discover_plugins", return_value=plugins):
        result = runner.invoke(app, ["completion", "regenerate", "--target", str(target)])
    assert result.exit_code == 0
    assert str(target) in result.output
    assert target.exists()
    assert "#compdef devkit" in target.read_text()
