from __future__ import annotations

import json
from typing import Any

from typer.testing import CliRunner

from devkit_encode.commands import decode_app, encode_app

runner = CliRunner()


# ── encode uuid ───────────────────────────────────────────────────────────────


def test_encode_uuid_produces_valid_uuid() -> None:
    result = runner.invoke(encode_app, ["uuid"])
    assert result.exit_code == 0
    u = result.output.strip()
    assert len(u) == 36
    assert u.count("-") == 4


def test_encode_uuid_count() -> None:
    result = runner.invoke(encode_app, ["uuid", "--count", "5"])
    assert result.exit_code == 0
    assert len(result.output.strip().splitlines()) == 5


def test_encode_uuid_json() -> None:
    result = runner.invoke(encode_app, ["uuid", "--count", "3", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) == 3


# ── encode base64 ─────────────────────────────────────────────────────────────


def test_encode_base64_encodes_string() -> None:
    result = runner.invoke(encode_app, ["base64", "hello"])
    assert result.exit_code == 0
    assert result.output.strip() == "aGVsbG8="


def test_encode_base64_json() -> None:
    result = runner.invoke(encode_app, ["base64", "hello", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["input"] == "hello"
    assert data["output"] == "aGVsbG8="


def test_encode_base64_stdin() -> None:
    result = runner.invoke(encode_app, ["base64"], input="hello\n")
    assert result.exit_code == 0
    assert result.output.strip() == "aGVsbG8="


# ── encode hash ───────────────────────────────────────────────────────────────


def test_encode_hash_string() -> None:
    result = runner.invoke(encode_app, ["hash", "hello"])
    assert result.exit_code == 0
    assert "md5" in result.output.lower() or "5d41402a" in result.output


def test_encode_hash_algo_sha256() -> None:
    result = runner.invoke(encode_app, ["hash", "hello", "--algo", "sha256"])
    assert result.exit_code == 0
    assert "2cf24dba" in result.output


def test_encode_hash_invalid_algo_exits_1() -> None:
    result = runner.invoke(encode_app, ["hash", "hello", "--algo", "md7"])
    assert result.exit_code == 1


def test_encode_hash_directory_exits_1(tmp_path: Any) -> None:
    result = runner.invoke(encode_app, ["hash", str(tmp_path)])
    assert result.exit_code == 1


def test_encode_hash_file(tmp_path: Any) -> None:
    f = tmp_path / "data.txt"
    f.write_text("hello")
    result = runner.invoke(encode_app, ["hash", str(f)])
    assert result.exit_code == 0
    assert "5d41402a" in result.output


def test_encode_hash_json(tmp_path: Any) -> None:
    f = tmp_path / "data.txt"
    f.write_text("hello")
    result = runner.invoke(encode_app, ["hash", str(f), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "md5" in data
    assert "sha256" in data


# ── encode timestamp ──────────────────────────────────────────────────────────


def test_encode_timestamp_current() -> None:
    result = runner.invoke(encode_app, ["timestamp"])
    assert result.exit_code == 0
    ts = int(result.output.strip())
    assert ts > 0


def test_encode_timestamp_converts() -> None:
    result = runner.invoke(encode_app, ["timestamp", "0"])
    assert result.exit_code == 0
    assert "1970" in result.output


def test_encode_timestamp_utc_flag() -> None:
    result = runner.invoke(encode_app, ["timestamp", "0", "--utc"])
    assert result.exit_code == 0
    assert "UTC" in result.output


def test_encode_timestamp_invalid_exits_1() -> None:
    result = runner.invoke(encode_app, ["timestamp", "notanumber"])
    assert result.exit_code == 1


def test_encode_timestamp_json() -> None:
    result = runner.invoke(encode_app, ["timestamp", "0", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["unix"] == 0
    assert "utc" in data


def test_encode_timestamp_out_of_range_exits_1() -> None:
    result = runner.invoke(encode_app, ["timestamp", "99999999999999"])
    assert result.exit_code == 1
    assert "range" in result.output.lower()


# ── encode format-json ────────────────────────────────────────────────────────


def test_encode_format_json_pretty() -> None:
    result = runner.invoke(encode_app, ["format-json"], input='{"a":1}')
    assert result.exit_code == 0
    assert "  " in result.output


def test_encode_format_json_compact() -> None:
    result = runner.invoke(encode_app, ["format-json", "--compact"], input='{"a": 1}')
    assert result.exit_code == 0
    assert result.output.strip() == '{"a":1}'


def test_encode_format_json_file(tmp_path: Any) -> None:
    f = tmp_path / "data.json"
    f.write_text('{"key": "value"}')
    result = runner.invoke(encode_app, ["format-json", str(f)])
    assert result.exit_code == 0
    assert '"key"' in result.output


def test_encode_format_json_invalid_exits_1() -> None:
    result = runner.invoke(encode_app, ["format-json"], input="{not valid}")
    assert result.exit_code == 1


# ── decode base64 ─────────────────────────────────────────────────────────────


def test_decode_base64_decodes() -> None:
    result = runner.invoke(decode_app, ["base64", "aGVsbG8="])
    assert result.exit_code == 0
    assert result.output.strip() == "hello"


def test_decode_base64_stdin() -> None:
    result = runner.invoke(decode_app, ["base64"], input="aGVsbG8=\n")
    assert result.exit_code == 0
    assert result.output.strip() == "hello"


def test_decode_base64_invalid_exits_1() -> None:
    result = runner.invoke(decode_app, ["base64", "!!!notbase64!!!"])
    assert result.exit_code == 1


def test_decode_base64_url_safe_exits_1() -> None:
    result = runner.invoke(decode_app, ["base64", "aGVs-bG8_"])
    assert result.exit_code == 1


def test_decode_base64_binary_payload_exits_1() -> None:
    import base64 as _b64

    binary_b64 = _b64.b64encode(bytes([0xFF, 0xFE, 0x00, 0x01])).decode()
    result = runner.invoke(decode_app, ["base64", binary_b64])
    assert result.exit_code == 1
    assert "UTF-8" in result.output or "binary" in result.output.lower()


def test_decode_base64_json() -> None:
    result = runner.invoke(decode_app, ["base64", "aGVsbG8=", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["output"] == "hello"


# ── decode timestamp ──────────────────────────────────────────────────────────


def test_decode_timestamp_iso() -> None:
    result = runner.invoke(decode_app, ["timestamp", "1970-01-01T00:00:00"])
    assert result.exit_code == 0
    assert result.output.strip() == "0"


def test_decode_timestamp_ambiguous_exits_1() -> None:
    result = runner.invoke(decode_app, ["timestamp", "01/02/03"])
    assert result.exit_code == 1


def test_decode_timestamp_invalid_exits_1() -> None:
    result = runner.invoke(decode_app, ["timestamp", "not-a-date"])
    assert result.exit_code == 1


def test_decode_timestamp_unknown_tz_exits_1() -> None:
    result = runner.invoke(decode_app, ["timestamp", "2026-01-01T00:00:00", "--tz", "Fake/Zone"])
    assert result.exit_code == 1


def test_decode_timestamp_json() -> None:
    result = runner.invoke(decode_app, ["timestamp", "1970-01-01T00:00:00", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["unix"] == 0
    assert "timezone" in data
