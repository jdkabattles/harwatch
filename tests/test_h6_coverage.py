"""H6 coverage tests for harwatch parse/runner/receipt edge cases.

Covers the lines the existing suite missed (full-suite coverage 0.7586 -> >= 0.8):
load errors, non-http skip, no-HTTP error, removed endpoint, status change,
invalid JSON body, list/bool/float shapes, endpoint merge + _union branches,
_missing_fields dict/list branches, count_fields list/scalar, main() incl. --out,
warnings, and the __main__ entry. Synthetic HARs only. No network. No secrets.
"""

from __future__ import annotations

import json
import runpy
import sys
from pathlib import Path

import pytest

from harwatch.parse import contract, diff, load
from harwatch.receipt import build_receipt
from harwatch.runner import main, run_check, scan_secrets


def entry(url: str, body: object = None, *, method: str = "GET",
          status: int = 200, headers: list | None = None,
          post_text: str | None = None, raw_text: str | None = None) -> dict:
    req: dict = {"method": method, "url": url, "headers": headers or []}
    if post_text is not None:
        req["postData"] = {"text": post_text}
    text = raw_text if raw_text is not None else (json.dumps(body) if body is not None else "")
    return {
        "request": req,
        "response": {"status": status, "content": {"text": text}},
    }


def har(entries: list[dict]) -> dict:
    return {"log": {"entries": entries}}


def write(tmp: Path, name: str, data: dict) -> Path:
    p = tmp / name
    p.write_text(json.dumps(data))
    return p


# ---- parse.load ----

def test_load_rejects_missing_log_entries(tmp_path: Path) -> None:
    p = write(tmp_path, "bad.har", {"log": {}})
    with pytest.raises(ValueError, match="missing log.entries"):
        load(p)


def test_load_rejects_missing_log(tmp_path: Path) -> None:
    p = write(tmp_path, "bad2.har", {})
    with pytest.raises(ValueError, match="missing log.entries"):
        load(p)


# ---- parse.contract ----

def test_contract_skips_non_http_url() -> None:
    c = contract(har([
        entry("ftp://files.example/data", {"x": 1}),
        entry("", {"x": 1}),
        entry("https://api.example/items", {"id": 1}),
    ]))
    assert list(c["endpoints"]) == ["GET /items"]


def test_contract_rejects_no_http_calls() -> None:
    with pytest.raises(ValueError, match="No HTTP calls"):
        contract(har([entry("ftp://files.example/data", {"x": 1})]))
    with pytest.raises(ValueError, match="No HTTP calls"):
        contract(har([]))


def test_contract_invalid_json_body_is_null_shape() -> None:
    c = contract(har([entry("https://api.example/items", raw_text="{not json")]))
    assert c["endpoints"]["GET /items"]["response"] == "null"


def test_contract_invalid_json_postdata_is_null_shape() -> None:
    c = contract(har([entry(
        "https://api.example/items", {"id": 1}, method="POST", post_text="{not json",
    )]))
    assert c["endpoints"]["POST /items"]["request"] == "null"


def test_contract_shape_list_bool_float_none_nested() -> None:
    body = {
        "tags": ["a", "b"],
        "active": True,
        "score": 1.5,
        "note": None,
        "matrix": [[1]],
        "empty": [],
    }
    c = contract(har([entry("https://api.example/items", body)]))
    shape = c["endpoints"]["GET /items"]["response"]
    assert shape == {
        "tags": ["string"],
        "active": "boolean",
        "score": "number",
        "note": "null",
        "matrix": [["integer"]],
        "empty": [],
    }


def test_contract_merges_duplicate_endpoint() -> None:
    c = contract(har([
        entry("https://api.example/items?x=1", {"id": 1}),
        entry("https://api.example/items?y=2", {"name": "a"}),
    ]))
    ep = c["endpoints"]["GET /items"]
    assert ep["query"] == ["x", "y"]
    assert ep["response"] == {"id": "integer", "name": "string"}
    assert ep["host"] == "api.example"
    assert ep["status"] == 200


def test_union_list_branches() -> None:
    # old empty list -> new list (106-107)
    c = contract(har([
        entry("https://api.example/a", []),
        entry("https://api.example/a", [1]),
    ]))
    assert c["endpoints"]["GET /a"]["response"] == ["integer"]
    # new empty list -> old list (108-109)
    c = contract(har([
        entry("https://api.example/b", [1]),
        entry("https://api.example/b", []),
    ]))
    assert c["endpoints"]["GET /b"]["response"] == ["integer"]
    # both non-empty lists -> recurse (110) + scalar fallback (111)
    c = contract(har([
        entry("https://api.example/c", [1]),
        entry("https://api.example/c", ["a"]),
    ]))
    assert c["endpoints"]["GET /c"]["response"] == ["integer"]


# ---- parse.diff ----

def _contract_for(entries: list[dict]) -> dict:
    return contract(har(entries))


def test_diff_removed_endpoint() -> None:
    old = _contract_for([
        entry("https://api.example/keep", {"id": 1}),
        entry("https://api.example/gone", {"id": 1}),
    ])
    new = _contract_for([entry("https://api.example/keep", {"id": 1})])
    assert diff(old, new) == ["removed GET /gone"]


def test_diff_status_change() -> None:
    old = _contract_for([entry("https://api.example/items", {"id": 1}, status=200)])
    new = _contract_for([entry("https://api.example/items", {"id": 1}, status=500)])
    assert diff(old, new) == ["status GET /items 200 -> 500"]


def test_diff_field_dict_becomes_scalar() -> None:
    old = _contract_for([entry("https://api.example/items", {"user": {"id": 1}})])
    new = _contract_for([entry("https://api.example/items", {"user": "x"})])
    assert diff(old, new) == ["removed field GET /items response.user"]


def test_diff_list_field_becomes_scalar() -> None:
    old = _contract_for([entry("https://api.example/items", [1, 2])])
    new = _contract_for([entry("https://api.example/items", {"id": 1})])
    assert diff(old, new) == ["removed field GET /items response.$"]


def test_diff_list_field_emptied() -> None:
    old = _contract_for([entry("https://api.example/items", [1])])
    new = _contract_for([entry("https://api.example/items", [])])
    assert diff(old, new) == ["removed field GET /items response.$"]


def test_diff_list_field_same_shape_no_break() -> None:
    old = _contract_for([entry("https://api.example/items", [1])])
    new = _contract_for([entry("https://api.example/items", ["a"])])
    assert diff(old, new) == []


# ---- receipt.count_fields ----

def _receipt_for(response_shape: object) -> dict:
    baseline = {
        "version": 1,
        "endpoints": {
            "GET /items": {
                "host": "api.example",
                "query": [],
                "status": 200,
                "response": response_shape,
                "request": {},
            }
        },
    }
    return build_receipt(
        baseline=baseline, baseline_hash="b" * 64, har_hash="h" * 64,
        breaks=[], check_id="hw-h6", timestamp="2026-10-18T00:00:00+00:00",
    )


def test_count_fields_list_response() -> None:
    r = _receipt_for(["integer"])
    assert r["fields_checked"] == 0  # list of scalars: no keys
    assert r["endpoints_checked"] == 1


def test_count_fields_nested_list_response() -> None:
    r = _receipt_for({"items": ["integer"], "total": "integer"})
    assert r["fields_checked"] == 2  # "items" + "total" keys; list scalars add 0


# ---- runner.main ----

def _files(tmp_path: Path) -> tuple[Path, Path]:
    base = contract(har([entry("https://api.example/items", {"id": 1})]))
    baseline_p = write(tmp_path, "baseline.json", base)
    submitted = har([entry("https://api.example/items", {"id": 2})])
    har_p = write(tmp_path, "submitted.har", submitted)
    return baseline_p, har_p


def test_main_stdout(monkeypatch, tmp_path: Path, capsys) -> None:
    baseline_p, har_p = _files(tmp_path)
    monkeypatch.setattr(sys, "argv", ["harwatch-check", str(baseline_p), str(har_p)])
    main()
    out = capsys.readouterr().out
    receipt = json.loads(out)
    assert receipt["result"] == "PASS"
    assert receipt["endpoints_checked"] == 1


def test_main_out_file(monkeypatch, tmp_path: Path, capsys) -> None:
    baseline_p, har_p = _files(tmp_path)
    out_p = tmp_path / "receipt.json"
    monkeypatch.setattr(
        sys, "argv",
        ["harwatch-check", str(baseline_p), str(har_p), "--out", str(out_p)],
    )
    main()
    out = capsys.readouterr().out
    assert "harwatch GOLD receipt" in out
    assert "PASS" in out
    receipt = json.loads(out_p.read_text())
    assert receipt["result"] == "PASS"


def test_main_warns_on_secrets(monkeypatch, tmp_path: Path, capsys) -> None:
    base = contract(har([entry("https://api.example/items", {"id": 1})]))
    baseline_p = write(tmp_path, "baseline.json", base)
    submitted = har([entry(
        "https://api.example/items?api_key=SECRET",
        {"id": 1},
        headers=[{"name": "Authorization", "value": "Bearer SECRET"}],
    )])
    har_p = write(tmp_path, "submitted.har", submitted)
    monkeypatch.setattr(sys, "argv", ["harwatch-check", str(baseline_p), str(har_p)])
    main()
    err = capsys.readouterr().err
    assert "authorization" in err
    assert "api_key" in err


def test_main_entry_point(monkeypatch, tmp_path: Path, capsys) -> None:
    # runpy re-executes the module as __main__ (covers `if __name__ == "__main__"`).
    baseline_p, har_p = _files(tmp_path)
    monkeypatch.setattr(sys, "argv", ["harwatch-check", str(baseline_p), str(har_p)])
    with pytest.warns(RuntimeWarning, match="found in sys.modules"):
        runpy.run_module("harwatch.runner", run_name="__main__")
    out = capsys.readouterr().out
    receipt = json.loads(out)
    assert receipt["result"] == "PASS"


def test_scan_secrets_query_only() -> None:
    h = har([entry("https://api.example/items?token=abc", {"id": 1})])
    warnings = scan_secrets(h)
    assert len(warnings) == 1
    assert "token" in warnings[0]


def test_run_check_removed_endpoint_is_fail(tmp_path: Path) -> None:
    base = contract(har([
        entry("https://api.example/keep", {"id": 1}),
        entry("https://api.example/gone", {"id": 1}),
    ]))
    baseline_p = write(tmp_path, "baseline.json", base)
    submitted = har([entry("https://api.example/keep", {"id": 1})])
    har_p = write(tmp_path, "submitted.har", submitted)
    receipt, _ = run_check(baseline_p, har_p)
    assert receipt["result"] == "FAIL"
    assert receipt["breaks"] == ["removed GET /gone"]
