from unittest.mock import patch

from devkit_core.spinner import _spinner_suppressed, run_with_spinner


def test_suppressed_when_ci(monkeypatch):
    monkeypatch.setenv("CI", "true")
    assert _spinner_suppressed() is True


def test_suppressed_when_no_color(monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")
    assert _spinner_suppressed() is True


def test_suppressed_when_non_tty():
    with patch("sys.stdout") as mock_stdout:
        mock_stdout.isatty.return_value = False
        assert _spinner_suppressed() is True


def test_not_suppressed_when_tty_and_no_env(monkeypatch):
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("NO_COLOR", raising=False)
    with patch("sys.stdout") as mock_stdout:
        mock_stdout.isatty.return_value = True
        assert _spinner_suppressed() is False


def test_run_with_spinner_returns_fn_result(monkeypatch):
    monkeypatch.setenv("CI", "true")
    result = run_with_spinner(lambda: 42, label="test")
    assert result == 42


def test_run_with_spinner_propagates_exception(monkeypatch):
    monkeypatch.setenv("CI", "true")

    def boom():
        raise ValueError("oops")

    import pytest
    with pytest.raises(ValueError, match="oops"):
        run_with_spinner(boom, label="test")
