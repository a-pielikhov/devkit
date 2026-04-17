from unittest.mock import MagicMock, patch

import pytest

from devkit_core.discovery import discover_plugins


def _make_ep(name: str, cls, dist_name: str = "devkit-fake"):
    ep = MagicMock()
    ep.name = name
    ep.value = f"{dist_name.replace('-', '_')}.commands:CommandGroup"
    ep.dist = MagicMock()
    ep.dist.name = dist_name
    ep.load.return_value = cls
    return ep


def _make_group_cls(name: str = "fake"):
    instance = MagicMock()
    instance.name = name
    instance.app = MagicMock()
    cls = MagicMock(return_value=instance)
    return cls


def test_discover_returns_loaded_groups():
    cls = _make_group_cls("fake")
    ep = _make_ep("fake", cls)

    with patch("devkit_core.discovery.entry_points", return_value=[ep]):
        groups = discover_plugins()

    assert len(groups) == 1
    assert groups[0].name == "fake"


def test_discover_returns_empty_when_no_entry_points():
    with patch("devkit_core.discovery.entry_points", return_value=[]):
        groups = discover_plugins()
    assert groups == []


def test_discover_conflict_exits_2():
    cls = _make_group_cls("git")
    ep1 = _make_ep("git", cls, "devkit-git")
    ep2 = _make_ep("git", cls, "devkit-mygit")

    with (
        patch("devkit_core.discovery.entry_points", return_value=[ep1, ep2]),
        pytest.raises(SystemExit) as exc_info,
    ):
        discover_plugins()
    assert exc_info.value.code == 2


def test_discover_broken_import_skips_and_loads_rest():
    # First EP raises on instantiation, second loads fine
    failing_cls = MagicMock(side_effect=ImportError("missing dep"))
    failing_ep = _make_ep("broken", failing_cls)

    working_cls = _make_group_cls("ok")
    working_ep = _make_ep("ok", working_cls)

    with patch("devkit_core.discovery.entry_points", return_value=[failing_ep, working_ep]):
        groups = discover_plugins()

    assert len(groups) == 1
    assert groups[0].name == "ok"


def test_discover_missing_protocol_attrs_skips():
    # Group instance missing 'app' attribute
    incomplete = MagicMock(spec=["name"])
    incomplete.name = "nope"
    cls = MagicMock(return_value=incomplete)
    ep = _make_ep("nope", cls)

    with patch("devkit_core.discovery.entry_points", return_value=[ep]):
        groups = discover_plugins()

    assert groups == []
