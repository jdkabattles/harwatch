import json
from pathlib import Path

from harwatch.parse import contract, diff, load

ROOT = Path(__file__).parent.parent / "examples"


def test_freeze_strips_and_counts():
    data = contract(load(ROOT / "before.har"))
    assert "GET /v1/orders" in data["endpoints"]
    assert "token" not in json.dumps(data)


def test_removed_field_breaks():
    old = contract(load(ROOT / "before.har"))
    new = contract(load(ROOT / "after.har"))
    breaks = diff(old, new)
    assert any("total" in item for item in breaks)


def test_same_shape_passes():
    old = contract(load(ROOT / "before.har"))
    assert diff(old, old) == []
