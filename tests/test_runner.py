"""Tests for paid check-runner. Synthetic HARs, no network, no secrets stored."""

from __future__ import annotations

import json
from pathlib import Path

from harwatch.parse import contract
from harwatch.runner import run_check, scan_secrets


def entry(url: str, body: dict | None, headers: list | None = None) -> dict:
    return {
        "request": {"method": "GET", "url": url, "headers": headers or []},
        "response": {"status": 200, "content": {"text": json.dumps(body) if body is not None else ""}},
    }


def har(entries: list[dict]) -> dict:
    return {"log": {"entries": entries}}


def write(tmp: Path, name: str, data: dict) -> Path:
    p = tmp / name
    p.write_text(json.dumps(data))
    return p


def test_runner_pass(tmp_path: Path) -> None:
    base_har = har([entry("https://api.example/items", {"id": 1, "name": "x"})])
    base = contract(base_har)
    baseline_p = write(tmp_path, "baseline.json", base)
    submitted = har([entry("https://api.example/items", {"id": 2, "name": "y"})])
    har_p = write(tmp_path, "submitted.har", submitted)
    receipt, warnings = run_check(baseline_p, har_p)
    assert receipt["result"] == "PASS"
    assert receipt["breaks"] == []
    assert receipt["endpoints_checked"] == 1
    assert warnings == []
    assert receipt["check_id"].startswith("hw-")
    assert len(receipt["baseline_hash"]) == 64
    assert len(receipt["har_hash"]) == 64


def test_runner_fail_on_removed_field(tmp_path: Path) -> None:
    base_har = har([entry("https://api.example/items", {"id": 1, "name": "x"})])
    base = contract(base_har)
    baseline_p = write(tmp_path, "baseline.json", base)
    submitted = har([entry("https://api.example/items", {"id": 2})])
    har_p = write(tmp_path, "submitted.har", submitted)
    receipt, _ = run_check(baseline_p, har_p)
    assert receipt["result"] == "FAIL"
    assert any("response.name" in b for b in receipt["breaks"])


def test_runner_warns_on_secrets(tmp_path: Path) -> None:
    base_har = har([entry("https://api.example/items", {"id": 1})])
    base = contract(base_har)
    baseline_p = write(tmp_path, "baseline.json", base)
    submitted = har([
        entry(
            "https://api.example/items?api_key=SECRET",
            {"id": 1},
            headers=[{"name": "Authorization", "value": "Bearer SECRET"}],
        )
    ])
    har_p = write(tmp_path, "submitted.har", submitted)
    receipt, warnings = run_check(baseline_p, har_p)
    assert any("authorization" in w for w in warnings)
    assert any("api_key" in w for w in warnings)
    # Contract never stores the secret value.
    assert "SECRET" not in json.dumps(receipt)
    assert "SECRET" not in json.dumps(base)


def test_scan_secrets_clean() -> None:
    assert scan_secrets(har([entry("https://api.example/items", {"id": 1})])) == []
