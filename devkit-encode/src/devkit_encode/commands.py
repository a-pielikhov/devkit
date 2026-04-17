from __future__ import annotations

from pathlib import Path

import typer

encode_app = typer.Typer(name="encode", help="Encoding and conversion")
decode_app = typer.Typer(name="decode", help="Decoding and conversion")


class EncodeCommandGroup:
    name = "encode"
    app = encode_app


class DecodeCommandGroup:
    name = "decode"
    app = decode_app


# ── encode uuid ───────────────────────────────────────────────────────────────

@encode_app.command("uuid")
def encode_uuid(
    count: int = typer.Option(1, "--count", help="Number of UUIDs to generate"),
    json_: bool = typer.Option(False, "--json", help="Output as JSON array"),
) -> None:
    """Generate one or more v4 UUIDs."""
    raise NotImplementedError


# ── encode base64 ─────────────────────────────────────────────────────────────

@encode_app.command("base64")
def encode_base64(
    string: str | None = typer.Argument(None, help="String to encode (reads stdin if omitted)"),
    json_: bool = typer.Option(False, "--json", help="Output as JSON with input/output fields"),
) -> None:
    """Encode <string> to base64."""
    raise NotImplementedError


# ── encode hash ───────────────────────────────────────────────────────────────

@encode_app.command("hash")
def encode_hash(
    input_: str | None = typer.Argument(None, metavar="string|file", help="String or file path"),
    algo: str | None = typer.Option(None, "--algo", help="Algorithm: md5, sha1, or sha256"),
    json_: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Compute md5, sha1, and sha256 of a string or file."""
    raise NotImplementedError


# ── encode timestamp ──────────────────────────────────────────────────────────

@encode_app.command("timestamp")
def encode_timestamp(
    unix_timestamp: int | None = typer.Argument(None, help="Unix timestamp (omit to print current)"),
    utc: bool = typer.Option(False, "--utc", help="Output UTC only"),
    json_: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Convert a Unix timestamp to human-readable datetime (or print current timestamp)."""
    raise NotImplementedError


# ── encode format-json ────────────────────────────────────────────────────────

@encode_app.command("format-json")
def encode_format_json(
    file: Path | None = typer.Argument(None, help="JSON file to format (reads stdin if omitted)"),
    compact: bool = typer.Option(False, "--compact", help="Output minified JSON"),
) -> None:
    """Pretty-print JSON from stdin or a file."""
    raise NotImplementedError


# ── decode base64 ─────────────────────────────────────────────────────────────

@decode_app.command("base64")
def decode_base64(
    string: str | None = typer.Argument(None, help="Base64 string to decode (reads stdin if omitted)"),
    json_: bool = typer.Option(False, "--json", help="Output as JSON with input/output fields"),
) -> None:
    """Decode <string> from base64."""
    raise NotImplementedError


# ── decode timestamp ──────────────────────────────────────────────────────────

@decode_app.command("timestamp")
def decode_timestamp(
    datetime_str: str = typer.Argument(..., metavar="datetime", help="Datetime string, e.g. 2026-01-01T00:00:00"),  # noqa: E501
    tz: str | None = typer.Option(None, "--tz", help="Timezone, e.g. Europe/Warsaw (default: UTC)"),
    json_: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Convert a human-readable datetime to a Unix timestamp."""
    raise NotImplementedError
