#!/usr/bin/env python3
"""Agent / human verification gate. Exit non-zero if any check fails."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str]) -> None:
    print("+", " ".join(command), flush=True)
    completed = subprocess.run(command, cwd=ROOT)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def main() -> int:
    run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"])
    run(["node", "--test", "tests/test_web_controls.mjs"])
    out = ROOT / "verify-smoke.jsonl"
    run([
        sys.executable, "-m", "lantern_islands",
        "--seed", "1", "--night", "2", "--ticks", "300", "--out", str(out),
    ])
    contract = json.loads((ROOT / "game.contract.json").read_text(encoding="utf-8"))
    assert contract["contract_version"] == "1.3"
    print("VERIFY OK", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
