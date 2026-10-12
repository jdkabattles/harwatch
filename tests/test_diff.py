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


def test_later_call_does_not_drop_an_earlier_field():
    har = {
        "log": {"entries": [
            {"request": {"method": "GET", "url": "https://a.test/v1/orders"},
             "response": {"status": 200, "content": {"text": '{"id":1,"total":2}'}}},
            {"request": {"method": "GET", "url": "https://a.test/v1/orders"},
             "response": {"status": 200, "content": {"text": '{"id":1}'}}},
        ]}
    }
    frozen = contract(har)
    assert "total" in frozen["endpoints"]["GET /v1/orders"]["response"]
    old = contract(load(ROOT / "before.har"))
    assert diff(old, old) == []
