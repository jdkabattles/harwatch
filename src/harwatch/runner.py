"""Paid harwatch check-runner. Manual fulfillment for MVP.

Takes a frozen baseline + a customer-submitted HAR, runs the check,
emits a GOLD receipt. Never stores the submitted HAR or any secrets.
Delete the submitted HAR after the check.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlparse

from .parse import SECRET_HEADERS, SECRET_QUERY, contract, diff, load
from .receipt import build_receipt, render_text, sha256_file, sha256_json


def scan_secrets(har: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    for i, entry in enumerate(har.get("log", {}).get("entries", [])):
        req = entry.get("request") or {}
        for h in req.get("headers") or []:
            name = (h.get("name") or "").lower()
            if name in SECRET_HEADERS:
                warnings.append(
                    f"entry {i}: header '{name}' present — redact before sending; not stored"
                )
        for name, _ in parse_qsl(urlparse(req.get("url") or "").query):
            if name.lower() in SECRET_QUERY:
                warnings.append(
                    f"entry {i}: query param '{name}' present — redact before sending; not stored"
                )
    return warnings


def run_check(
    baseline_path: str | Path, har_path: str | Path
) -> tuple[dict[str, Any], list[str]]:
    submitted = Path(har_path)
    try:
        baseline = json.loads(Path(baseline_path).read_text())
        baseline_hash = sha256_json(baseline)
        har_hash = sha256_file(str(submitted))
        har = load(submitted)
        warnings = scan_secrets(har)
        new = contract(har)
        breaks = diff(baseline, new)
        ts = datetime.now(timezone.utc)
        check_id = f"hw-{ts.strftime('%Y%m%dT%H%M%SZ')}-{har_hash[:8]}"
        receipt = build_receipt(
            baseline=baseline,
            baseline_hash=baseline_hash,
            har_hash=har_hash,
            breaks=breaks,
            check_id=check_id,
            timestamp=ts.isoformat(),
        )
        return receipt, warnings
    finally:
        # S5 (HAR delete-after-check): the submitted HAR is deleted on every
        # path out of the check — pass, fail verdict, or exception — so a
        # customer file is never left on disk. The receipt keeps hashes only.
        submitted.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(prog="harwatch-check")
    parser.add_argument("baseline", help="Frozen contract.json")
    parser.add_argument("har", help="Customer-submitted HAR (delete after check, never store)")
    parser.add_argument("--out", default=None, help="Write receipt JSON here (default: stdout)")
    args = parser.parse_args()
    receipt, warnings = run_check(args.baseline, args.har)
    for w in warnings:
        print(f"WARNING: {w}", file=sys.stderr)
    if args.out:
        Path(args.out).write_text(json.dumps(receipt, indent=2) + "\n")
        print(render_text(receipt))
    else:
        print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
