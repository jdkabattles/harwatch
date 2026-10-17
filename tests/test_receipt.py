"""Tests for GOLD receipt."""

from __future__ import annotations

import json

from harwatch.receipt import build_receipt, render_text, sha256_json


def baseline() -> dict:
    return {
        "version": 1,
        "endpoints": {
            "GET /api/items": {
                "host": "api.example",
                "query": [],
                "status": 200,
                "response": {"id": "integer", "name": "string"},
                "request": {},
            }
        },
    }


def test_receipt_pass() -> None:
    r = build_receipt(
        baseline=baseline(), baseline_hash="b" * 64, har_hash="h" * 64,
        breaks=[], check_id="hw-1", timestamp="2026-10-17T00:00:00+00:00",
    )
    assert r["result"] == "PASS"
    assert r["endpoints_checked"] == 1
    assert r["fields_checked"] == 2
    assert r["breaks"] == []


def test_receipt_fail_lists_breaks() -> None:
    r = build_receipt(
        baseline=baseline(), baseline_hash="b" * 64, har_hash="h" * 64,
        breaks=["removed field GET /api/items response.name"],
        check_id="hw-2", timestamp="2026-10-17T00:00:00+00:00",
    )
    assert r["result"] == "FAIL"
    assert r["breaks"] == ["removed field GET /api/items response.name"]
    text = render_text(r)
    assert "FAIL" in text and "removed field" in text


def test_sha256_json_is_canonical() -> None:
    assert sha256_json({"b": 1, "a": 2}) == sha256_json({"a": 2, "b": 1})
    assert len(sha256_json({})) == 64
