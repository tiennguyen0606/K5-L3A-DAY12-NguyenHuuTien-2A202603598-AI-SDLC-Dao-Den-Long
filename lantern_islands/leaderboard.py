from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import re
from typing import Any


NAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,12}$")
DEFAULT_PATH = Path("data/leaderboard.json")


class LeaderboardStore:
    def __init__(self, path: Path = DEFAULT_PATH):
        self.path = path

    def entries(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        entries = data.get("entries", []) if isinstance(data, dict) else []
        return sorted(entries, key=lambda item: (-int(item["score"]), item["achieved_at"]))[:10]

    def add(self, entry: dict[str, Any]) -> list[dict[str, Any]]:
        name = str(entry.get("name", ""))
        if not NAME_PATTERN.fullmatch(name):
            raise ValueError("name must be 3-12 characters using A-Z, a-z, 0-9, or underscore")
        score = int(entry.get("score", -1))
        nights_won = int(entry.get("nights_won", -1))
        seed = int(entry.get("seed", 0))
        achieved_at = str(entry.get("achieved_at", ""))
        try:
            parsed = datetime.fromisoformat(achieved_at)
        except ValueError as error:
            raise ValueError("achieved_at must be ISO 8601") from error
        if parsed.tzinfo is None or score < 0 or not 0 <= nights_won <= 3:
            raise ValueError("invalid leaderboard entry")
        clean = {"name": name, "score": score, "nights_won": nights_won, "achieved_at": achieved_at, "seed": seed}
        entries = sorted(self.entries() + [clean], key=lambda item: (-item["score"], item["achieved_at"]))[:10]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"entries": entries}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return entries

    def export(self, target: Path) -> None:
        target.write_text(json.dumps({"entries": self.entries()}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--export-leaderboard", metavar="OUT")
    parser.add_argument("--data", default=str(DEFAULT_PATH))
    args = parser.parse_args(argv)
    if args.export_leaderboard:
        LeaderboardStore(Path(args.data)).export(Path(args.export_leaderboard))
        return 0
    parser.error("--export-leaderboard is required")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

