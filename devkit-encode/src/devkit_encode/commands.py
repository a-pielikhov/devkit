from __future__ import annotations

import base64 as _base64
import binascii
import hashlib
import json
import re
import sys
import time
import uuid as _uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import typer

from devkit_core.output import print_error, print_table
from devkit_core.spinner import run_with_spinner

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
    uuids = [str(_uuid.uuid4()) for _ in range(count)]
    if json_:
        typer.echo(json.dumps(uuids))
    else:
        for u in uuids:
            typer.echo(u)


# ── encode base64 ─────────────────────────────────────────────────────────────


@encode_app.command("base64")
def encode_base64(
    string: str | None = typer.Argument(None, help="String to encode (reads stdin if omitted)"),
    json_: bool = typer.Option(False, "--json", help="Output as JSON with input/output fields"),
) -> None:
    """Encode <string> to base64."""
    if string is None:
        raw = sys.stdin.read()
        if raw.endswith("\r\n"):
            raw = raw[:-2]
        elif raw.endswith("\n"):
            raw = raw[:-1]
    else:
        raw = string
    encoded = _base64.b64encode(raw.encode()).decode()
    if json_:
        typer.echo(json.dumps({"input": raw, "output": encoded}))
    else:
        typer.echo(encoded)


# ── encode hash ───────────────────────────────────────────────────────────────

_ALGOS: tuple[str, ...] = ("md5", "sha1", "sha256")


@encode_app.command("hash")
def encode_hash(
    input_: str | None = typer.Argument(None, metavar="string|file", help="String or file path"),
    algo: str | None = typer.Option(None, "--algo", help="Algorithm: md5, sha1, or sha256"),
    json_: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Compute md5, sha1, and sha256 of a string or file."""
    if algo is not None and algo not in _ALGOS:
        print_error(f"Unknown algorithm '{algo}'. Choose from: {', '.join(_ALGOS)}")
        raise typer.Exit(1)

    algos_to_run: tuple[str, ...] = (algo,) if algo else _ALGOS

    data: bytes
    if input_ is None:
        data = sys.stdin.buffer.read()
    else:
        p = Path(input_)
        if p.is_dir():
            print_error(f"{input_!r} is a directory, not a file")
            raise typer.Exit(1)
        if p.is_file():
            data = run_with_spinner(p.read_bytes, label=f"Hashing {p.name}...")
        else:
            data = input_.encode()

    results: dict[str, str] = {a: hashlib.new(a, data).hexdigest() for a in algos_to_run}

    if json_:
        typer.echo(json.dumps(results))
    else:
        print_table(["Algorithm", "Hash"], [(a, results[a]) for a in algos_to_run])


# ── encode timestamp ──────────────────────────────────────────────────────────


@encode_app.command("timestamp")
def encode_timestamp(
    unix_timestamp: str | None = typer.Argument(
        None, metavar="unix_timestamp", help="Unix timestamp (omit to print current)"
    ),
    utc: bool = typer.Option(False, "--utc", help="Output UTC only"),
    json_: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Convert a Unix timestamp to human-readable datetime (or print current timestamp)."""
    if unix_timestamp is None:
        ts = int(time.time())
        if json_:
            typer.echo(json.dumps({"unix": ts}))
        else:
            typer.echo(str(ts))
        return

    try:
        ts = int(unix_timestamp)
    except ValueError:
        print_error(f"{unix_timestamp!r} is not a valid integer")
        raise typer.Exit(1) from None

    try:
        utc_dt = datetime.fromtimestamp(ts, tz=UTC)
    except (OSError, OverflowError, ValueError):
        print_error(f"Timestamp {ts} is out of the supported range")
        raise typer.Exit(1) from None
    utc_str = utc_dt.strftime("%Y-%m-%d %H:%M:%S UTC")

    if json_:
        result: dict[str, Any] = {"unix": ts, "utc": utc_str}
        if not utc:
            local_dt = datetime.fromtimestamp(ts).astimezone()
            result["local"] = local_dt.strftime("%Y-%m-%d %H:%M:%S %Z")
        typer.echo(json.dumps(result))
    elif utc:
        typer.echo(utc_str)
    else:
        local_dt = datetime.fromtimestamp(ts).astimezone()
        local_str = local_dt.strftime("%Y-%m-%d %H:%M:%S %Z")
        print_table(["Zone", "Datetime"], [("UTC", utc_str), ("Local", local_str)])


# ── encode format-json ────────────────────────────────────────────────────────


@encode_app.command("format-json")
def encode_format_json(
    file: Path | None = typer.Argument(None, help="JSON file to format (reads stdin if omitted)"),
    compact: bool = typer.Option(False, "--compact", help="Output minified JSON"),
) -> None:
    """Pretty-print JSON from stdin or a file."""
    raw = file.read_text() if file is not None else sys.stdin.read()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print_error(f"Invalid JSON: {exc.msg} at line {exc.lineno}, column {exc.colno}")
        raise typer.Exit(1) from None

    if compact:
        typer.echo(json.dumps(data, separators=(",", ":")))
    else:
        typer.echo(json.dumps(data, indent=2))


# ── decode base64 ─────────────────────────────────────────────────────────────


@decode_app.command("base64")
def decode_base64(
    string: str | None = typer.Argument(None, help="Base64 string to decode (reads stdin if omitted)"),
    json_: bool = typer.Option(False, "--json", help="Output as JSON with input/output fields"),
) -> None:
    """Decode <string> from base64."""
    if string is None:
        raw = sys.stdin.read()
        if raw.endswith("\r\n"):
            raw = raw[:-2]
        elif raw.endswith("\n"):
            raw = raw[:-1]
    else:
        raw = string

    if "-" in raw or "_" in raw:
        print_error("URL-safe base64 is not supported. Replace - with + and _ with / before decoding.")
        raise typer.Exit(1)

    try:
        decoded_bytes = _base64.b64decode(raw.encode(), validate=True)
    except (binascii.Error, ValueError):
        print_error(f"{raw!r} is not valid base64")
        raise typer.Exit(1) from None

    try:
        decoded = decoded_bytes.decode()
    except UnicodeDecodeError:
        print_error("Decoded content is not valid UTF-8 (binary data?)")
        raise typer.Exit(1) from None

    if json_:
        typer.echo(json.dumps({"input": raw, "output": decoded}))
    else:
        typer.echo(decoded)


# ── decode timestamp ──────────────────────────────────────────────────────────

_AMBIGUOUS_RE = re.compile(r"^\d{1,2}[/.\-]\d{1,2}[/.\-]\d{2,4}$")


@decode_app.command("timestamp")
def decode_timestamp(
    datetime_str: str = typer.Argument(
        ..., metavar="datetime", help="Datetime string, e.g. 2026-01-01T00:00:00"
    ),
    tz: str | None = typer.Option(None, "--tz", help="Timezone, e.g. Europe/Warsaw (default: UTC)"),
    json_: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Convert a human-readable datetime to a Unix timestamp."""
    if _AMBIGUOUS_RE.match(datetime_str):
        print_error("Ambiguous format. Use ISO 8601: YYYY-MM-DD HH:MM:SS")
        raise typer.Exit(1)

    try:
        dt_naive = datetime.fromisoformat(datetime_str)
    except ValueError:
        print_error(f"Cannot parse {datetime_str!r} as a valid datetime string")
        raise typer.Exit(1) from None

    tz_label: str
    if dt_naive.tzinfo is not None:
        dt_aware = dt_naive
        tz_label = str(dt_naive.tzinfo)
    elif tz:
        try:
            tz_obj = ZoneInfo(tz)
        except (ZoneInfoNotFoundError, KeyError):
            print_error(f"Unknown timezone '{tz}'. Use IANA format, e.g. Europe/Warsaw")
            raise typer.Exit(1) from None
        dt_aware = dt_naive.replace(tzinfo=tz_obj)
        roundtrip = dt_aware.astimezone(tz_obj)
        if roundtrip.replace(tzinfo=None) != dt_naive:
            print_error(
                f"The datetime {datetime_str!r} falls in a DST gap in timezone {tz!r}. "
                "This local time does not exist (spring-forward transition)."
            )
            raise typer.Exit(1)
        tz_label = tz
    else:
        dt_aware = dt_naive.replace(tzinfo=UTC)
        tz_label = "UTC"

    ts = int(dt_aware.timestamp())

    if json_:
        typer.echo(json.dumps({"datetime": datetime_str, "timezone": tz_label, "unix": ts}))
    else:
        typer.echo(str(ts))
