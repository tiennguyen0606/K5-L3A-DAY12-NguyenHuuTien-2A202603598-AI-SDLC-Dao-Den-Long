import json
from pathlib import Path
import tempfile
import unittest

from lantern_islands.benchmark import calculate_metrics
from lantern_islands.leaderboard import LeaderboardStore
from lantern_islands.soak import run_soak


class Phase4ReleaseTests(unittest.TestCase):
    def test_benchmark_metrics_follow_contract_formulas(self):
        metrics = calculate_metrics([10.0] * 99 + [100.0])
        self.assertEqual(metrics["frames"], 100)
        self.assertAlmostEqual(metrics["avg_fps"], 1000 * 100 / 1090, places=3)
        self.assertEqual(metrics["p1_low_fps"], 10.0)
        self.assertEqual(metrics["frame_ms_p95"], 10.0)

    def test_leaderboard_validates_sorts_and_keeps_top_ten(self):
        with tempfile.TemporaryDirectory() as directory:
            store = LeaderboardStore(Path(directory) / "leaderboard.json")
            for index in range(12):
                store.add({
                    "name": f"P{index:02}", "score": index * 10, "nights_won": index % 4,
                    "achieved_at": f"2026-11-20T10:{index:02}:00+07:00", "seed": 42,
                })
            entries = store.entries()
            self.assertEqual(len(entries), 10)
            self.assertEqual(entries[0]["name"], "P11")
            self.assertEqual(entries[-1]["name"], "P02")
            with self.assertRaises(ValueError):
                store.add({"name": "bad name!", "score": 1, "nights_won": 0, "achieved_at": "x", "seed": 1})

    def test_soak_is_deterministic_and_reports_no_crashes(self):
        first = run_soak(seed=7, nights=2)
        second = run_soak(seed=7, nights=2)
        self.assertEqual(first["results"], second["results"])
        self.assertEqual(first["crashes"], 0)
        self.assertEqual(first["nights"], 2)
        self.assertLessEqual(first["mem_end_mb"], first["mem_start_mb"] * 1.2)


if __name__ == "__main__":
    unittest.main()
