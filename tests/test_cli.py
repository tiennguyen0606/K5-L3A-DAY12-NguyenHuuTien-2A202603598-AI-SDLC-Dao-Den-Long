import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class HeadlessCliTests(unittest.TestCase):
    def test_writes_tick_zero_periodic_snapshots_and_end(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "run.jsonl"
            result = subprocess.run(
                [sys.executable, "-m", "lantern_islands", "--seed", "12", "--night", "1", "--ticks", "20", "--out", str(output), "--snapshot-every", "10"],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
            self.assertEqual([row["tick"] for row in rows if row["type"] == "snapshot"], [0, 10, 20])
            self.assertEqual(rows[-1], {"type": "end", "ticks": 20, "state": "playing", "score": 0})

    def test_invalid_scenario_returns_contract_error_code_two(self):
        with tempfile.TemporaryDirectory() as directory:
            scenario = Path(directory) / "bad.json"
            scenario.write_text("not-json", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-m", "lantern_islands", "--seed", "1", "--night", "1", "--ticks", "1", "--out", str(Path(directory) / "out.jsonl"), "--scenario", str(scenario)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("scenario", result.stderr.lower())


if __name__ == "__main__":
    unittest.main()
