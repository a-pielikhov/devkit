from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from devkit_file.commands import app

runner = CliRunner()


# ── find-duplicates ───────────────────────────────────────────────────────────


def test_find_duplicates_groups_identical_files(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("same")
    (tmp_path / "b.txt").write_text("same")
    (tmp_path / "c.txt").write_text("different")
    result = runner.invoke(app, ["find-duplicates", str(tmp_path)])
    assert result.exit_code == 0
    assert "Group" in result.output


def test_find_duplicates_no_duplicates(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("hello")
    (tmp_path / "b.txt").write_text("world")
    result = runner.invoke(app, ["find-duplicates", str(tmp_path)])
    assert result.exit_code == 0
    assert "No duplicates" in result.output


def test_find_duplicates_empty_files_skipped(tmp_path: Path) -> None:
    (tmp_path / "empty1.txt").write_text("")
    (tmp_path / "empty2.txt").write_text("")
    result = runner.invoke(app, ["find-duplicates", str(tmp_path)])
    assert result.exit_code == 0
    assert "empty" in result.output.lower()


def test_find_duplicates_json(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("same")
    (tmp_path / "b.txt").write_text("same")
    result = runner.invoke(app, ["find-duplicates", str(tmp_path), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) == 1
    assert len(data[0]) == 2


def test_find_duplicates_delete(tmp_path: Path, monkeypatch: Any) -> None:
    (tmp_path / "a.txt").write_text("same")
    (tmp_path / "b.txt").write_text("same")
    result = runner.invoke(app, ["find-duplicates", str(tmp_path), "--delete"], input="y\n")
    assert result.exit_code == 0
    remaining = list(tmp_path.glob("*.txt"))
    assert len(remaining) == 1


# ── find-large-files ──────────────────────────────────────────────────────────


def test_find_large_files_lists_above_threshold(tmp_path: Path) -> None:
    (tmp_path / "big.txt").write_bytes(b"x" * 2048)
    (tmp_path / "small.txt").write_bytes(b"x" * 10)
    result = runner.invoke(app, ["find-large-files", str(tmp_path), "--min-size", "1KB", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    paths = [item["path"] for item in data]
    assert any("big.txt" in p for p in paths)
    assert all("small.txt" not in p for p in paths)


def test_find_large_files_no_match(tmp_path: Path) -> None:
    (tmp_path / "tiny.txt").write_bytes(b"x" * 5)
    result = runner.invoke(app, ["find-large-files", str(tmp_path), "--min-size", "1MB"])
    assert result.exit_code == 0
    assert "No files found" in result.output


def test_find_large_files_top_limit(tmp_path: Path) -> None:
    for i in range(5):
        (tmp_path / f"f{i}.txt").write_bytes(b"x" * (1024 * (i + 1)))
    result = runner.invoke(
        app, ["find-large-files", str(tmp_path), "--min-size", "1KB", "--top", "3", "--json"]
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 3


def test_find_large_files_top_zero_exits_1(tmp_path: Path) -> None:
    result = runner.invoke(app, ["find-large-files", str(tmp_path), "--top", "0"])
    assert result.exit_code == 1


def test_find_large_files_invalid_size_exits_1(tmp_path: Path) -> None:
    result = runner.invoke(app, ["find-large-files", str(tmp_path), "--min-size", "10gigabytes"])
    assert result.exit_code == 1


def test_find_large_files_ext_filter(tmp_path: Path) -> None:
    (tmp_path / "big.log").write_bytes(b"x" * 2048)
    (tmp_path / "big.txt").write_bytes(b"x" * 2048)
    result = runner.invoke(
        app, ["find-large-files", str(tmp_path), "--min-size", "1KB", "--ext", ".log", "--json"]
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    paths = [item["path"] for item in data]
    assert any("big.log" in p for p in paths)
    assert all("big.txt" not in p for p in paths)


def test_find_large_files_json(tmp_path: Path) -> None:
    (tmp_path / "big.txt").write_bytes(b"x" * 2048)
    result = runner.invoke(app, ["find-large-files", str(tmp_path), "--min-size", "1KB", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) == 1
    assert "size_bytes" in data[0]
    assert "size_human" in data[0]
