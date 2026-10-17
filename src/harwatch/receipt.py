"""GOLD receipt for one harwatch check. No secrets, no fake numbers."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def sha256_json(value: Any) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def count_fields(shape: Any) -> int:
    # A field is a key at any depth. Leaf scalars are values, not fields.
    if isinstance(shape, dict):
        return len(shape) + sum(
            count_fields(v) for v in shape.values() if isinstance(v, (dict, list))
        )
    if isinstance(shape, list):
        return sum(count_fields(v) for v in shape)
    return 0


def build_receipt(
    *,
    baseline: dict[str, Any],
    baseline_hash: str,
    har_hash: str,
    breaks: list[str],
    check_id: str,
    timestamp: str,
) -> dict[str, Any]:
    endpoints = baseline.get("endpoints") or {}
    fields = sum(count_fields(ep.get("response")) for ep in endpoints.values())
    return {
        "check_id": check_id,
        "timestamp": timestamp,
        "result": "FAIL" if breaks else "PASS",
        "baseline_hash": baseline_hash,
        "har_hash": har_hash,
        "endpoints_checked": len(endpoints),
        "fields_checked": fields,
        "breaks": list(breaks),
    }


def render_text(receipt: dict[str, Any]) -> str:
    lines = [
        "harwatch GOLD receipt",
        f"check: {receipt['check_id']}",
        f"timestamp: {receipt['timestamp']}",
        f"result: {receipt['result']}",
        f"baseline: {receipt['baseline_hash']}",
        f"submitted HAR: {receipt['har_hash']}",
        f"endpoints checked: {receipt['endpoints_checked']}",
        f"fields checked: {receipt['fields_checked']}",
    ]
    if receipt["breaks"]:
        lines.append("breaks:")
        lines.extend(f"- {b}" for b in receipt["breaks"])
    return "\n".join(lines) + "\n"
