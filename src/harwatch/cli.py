"""harwatch freeze | check."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .parse import contract, diff, load


def main() -> None:
    parser = argparse.ArgumentParser(prog="harwatch")
    sub = parser.add_subparsers(dest="cmd", required=True)

    freeze = sub.add_parser("freeze", help="Write contract.json from a HAR")
    freeze.add_argument("har")
    freeze.add_argument("--out", default="contract.json")

    check = sub.add_parser("check", help="Fail if a new HAR breaks the contract")
    check.add_argument("har")
    check.add_argument("--contract", default="contract.json")

    args = parser.parse_args()
    if args.cmd == "freeze":
        data = contract(load(args.har))
        Path(args.out).write_text(json.dumps(data, indent=2) + "\n")
        print(f"endpoints={len(data['endpoints'])} out={args.out}")
        return
    old = json.loads(Path(args.contract).read_text())
    breaks = diff(old, contract(load(args.har)))
    if breaks:
        print("BREAK")
        for item in breaks:
            print(f"- {item}")
        sys.exit(1)
    print("OK")


if __name__ == "__main__":
    main()
