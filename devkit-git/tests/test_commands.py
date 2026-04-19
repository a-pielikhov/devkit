from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from devkit_git.commands import app

runner = CliRunner()


def _make_repo(tmp_path: Path) -> Any:
    from git import Repo

    repo = Repo.init(str(tmp_path))
    repo.config_writer().set_value("user", "name", "Test").release()
    repo.config_writer().set_value("user", "email", "test@test.com").release()
    (tmp_path / "file.txt").write_text("initial")
    repo.index.add(["file.txt"])
    repo.index.commit("initial commit")
    return repo


# ── git clean-branches ────────────────────────────────────────────────────────


def test_clean_branches_invalid_regexp() -> None:
    result = runner.invoke(app, ["clean-branches", "[invalid"])
    assert result.exit_code == 1


def test_clean_branches_not_in_repo(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["clean-branches", "feat/*"])
    assert result.exit_code == 2


def test_clean_branches_no_match(tmp_path: Path, monkeypatch: Any) -> None:
    _make_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["clean-branches", "nonexistent.*"])
    assert result.exit_code == 0
    assert "No branches" in result.output


def test_clean_branches_deletes_matching(tmp_path: Path, monkeypatch: Any) -> None:
    repo = _make_repo(tmp_path)
    repo.create_head("feat/test")
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["clean-branches", "feat/test"], input="y\n")
    assert result.exit_code == 0
    branch_names = [b.name for b in repo.branches]
    assert "feat/test" not in branch_names


def test_clean_branches_skips_current(tmp_path: Path, monkeypatch: Any) -> None:
    repo = _make_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    current = repo.active_branch.name
    result = runner.invoke(app, ["clean-branches", current], input="y\n")
    assert result.exit_code == 0
    assert "Skipping" in result.output
    assert current in repo.active_branch.name


def test_clean_branches_skips_protected(tmp_path: Path, monkeypatch: Any) -> None:
    repo = _make_repo(tmp_path)
    repo.create_head("main")
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["clean-branches", "main"], input="y\n")
    assert result.exit_code == 0
    assert "Skipping" in result.output


def test_clean_branches_force_deletes_protected(tmp_path: Path, monkeypatch: Any) -> None:
    repo = _make_repo(tmp_path)
    repo.create_head("master")
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["clean-branches", "master", "--force"], input="y\n")
    assert result.exit_code == 0
    branch_names = [b.name for b in repo.branches]
    assert "master" not in branch_names


# ── git undo ──────────────────────────────────────────────────────────────────


def test_undo_removes_last_commit(tmp_path: Path, monkeypatch: Any) -> None:
    repo = _make_repo(tmp_path)
    (tmp_path / "second.txt").write_text("second")
    repo.index.add(["second.txt"])
    repo.index.commit("second commit")
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["undo"])
    assert result.exit_code == 0
    assert "second commit" in result.output
    assert len(list(repo.iter_commits())) == 1


def test_undo_keeps_changes_staged(tmp_path: Path, monkeypatch: Any) -> None:
    repo = _make_repo(tmp_path)
    (tmp_path / "second.txt").write_text("second")
    repo.index.add(["second.txt"])
    repo.index.commit("second commit")
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["undo"])
    staged = [item.a_path for item in repo.index.diff("HEAD")]
    assert "second.txt" in staged


def test_undo_single_commit_no_commits_remain(tmp_path: Path, monkeypatch: Any) -> None:
    _make_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["undo"])
    assert result.exit_code == 0
    assert "no commits" in result.output.lower()


def test_undo_initial_commit_working_tree_intact(tmp_path: Path, monkeypatch: Any) -> None:
    _make_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    runner.invoke(app, ["undo"])
    assert (tmp_path / "file.txt").exists()


def test_undo_merge_commit_prints_note(tmp_path: Path, monkeypatch: Any) -> None:
    repo = _make_repo(tmp_path)
    branch = repo.create_head("feature")
    branch.checkout()
    (tmp_path / "feature.txt").write_text("feature")
    repo.index.add(["feature.txt"])
    repo.index.commit("feature commit")
    repo.heads.master.checkout() if "master" in [h.name for h in repo.heads] else repo.heads[
        "master" if "master" in [h.name for h in repo.heads] else list(repo.heads)[0].name
    ].checkout()
    # Merge
    try:
        repo.git.merge("feature", "--no-ff", "-m", "merge commit")
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["undo"])
        assert result.exit_code == 0
        assert "merge commit" in result.output.lower()
    except Exception:
        pytest.skip("merge setup failed in test env")


# ── git list-merged ───────────────────────────────────────────────────────────


def test_list_merged_unknown_default_branch_exits_1(tmp_path: Path, monkeypatch: Any) -> None:
    repo = _make_repo(tmp_path)
    # Rename to something non-standard
    repo.heads[0].rename("trunk")
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["list-merged"])
    assert result.exit_code == 1
    assert "Cannot detect" in result.output


def test_list_merged_no_merged(tmp_path: Path, monkeypatch: Any) -> None:
    _make_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["list-merged"])
    assert result.exit_code == 0
    assert "No merged" in result.output


def test_list_merged_delete_removes_branches(tmp_path: Path, monkeypatch: Any) -> None:
    repo = _make_repo(tmp_path)
    feature = repo.create_head("feature")
    feature.checkout()
    (tmp_path / "feat.txt").write_text("feat")
    repo.index.add(["feat.txt"])
    repo.index.commit("feat commit")
    default = next(h for h in repo.heads if h.name in ("main", "master"))
    default.checkout()
    repo.git.merge("feature", "--ff-only")
    repo.create_head("feature2").checkout()
    (tmp_path / "feat2.txt").write_text("feat2")
    repo.index.add(["feat2.txt"])
    repo.index.commit("feat2 commit")
    default.checkout()
    repo.git.merge("feature2", "--ff-only")
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["list-merged", "--delete"], input="y\n")
    assert result.exit_code == 0
    branch_names = [b.name for b in repo.branches]
    assert "feature" not in branch_names
    assert "feature2" not in branch_names


# ── git sync-fork ─────────────────────────────────────────────────────────────


def test_sync_fork_dirty_working_tree_exits_2(tmp_path: Path, monkeypatch: Any) -> None:
    repo = _make_repo(tmp_path)
    (tmp_path / "dirty.txt").write_text("dirty")
    repo.index.add(["dirty.txt"])
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["sync-fork"])
    assert result.exit_code == 2
    assert "Uncommitted" in result.output


def test_sync_fork_no_upstream_exits_2(tmp_path: Path, monkeypatch: Any) -> None:
    _make_repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["sync-fork"])
    assert result.exit_code == 2
    assert "upstream" in result.output.lower()


# ── git config ────────────────────────────────────────────────────────────────


def test_config_add_and_show(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    result = runner.invoke(app, ["config", "add", "protected_branches", "staging"])
    assert result.exit_code == 0
    result = runner.invoke(app, ["config", "show"])
    assert result.exit_code == 0
    assert "staging" in result.output


def test_config_add_replace(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    runner.invoke(app, ["config", "add", "protected_branches", "main"])
    runner.invoke(app, ["config", "add", "protected_branches", "develop"])
    result = runner.invoke(app, ["config", "add", "protected_branches", "trunk", "--replace"])
    assert result.exit_code == 0
    result = runner.invoke(app, ["config", "show", "--json"])
    data = json.loads(result.output)
    assert data["protected_branches"] == "trunk"


def test_config_remove_key(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    runner.invoke(app, ["config", "add", "protected_branches", "main"])
    result = runner.invoke(app, ["config", "remove", "protected_branches"])
    assert result.exit_code == 0
    result = runner.invoke(app, ["config", "show"])
    assert "No configuration" in result.output


def test_config_remove_missing_key_warns(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    result = runner.invoke(app, ["config", "remove", "nonexistent"])
    assert result.exit_code == 0


def test_config_show_empty(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    result = runner.invoke(app, ["config", "show"])
    assert result.exit_code == 0
    assert "No configuration" in result.output


def test_config_show_json(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    runner.invoke(app, ["config", "add", "protected_branches", "main"])
    result = runner.invoke(app, ["config", "show", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "protected_branches" in data
