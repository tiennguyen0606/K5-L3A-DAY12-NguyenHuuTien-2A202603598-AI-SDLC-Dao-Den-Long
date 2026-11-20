# Phase 4 proof

Run:

```bash
python3 -m unittest tests/test_phase4.py -v
python3 -m unittest discover -s tests -v
python3 -m lantern_islands.benchmark --seed 42 --duration 30 --out bench.json
python3 -m lantern_islands.soak --seed 7 --nights 10 --out soak.json
python3 -m lantern_islands.webapp --export-leaderboard leaderboard-export.json
```

| Requirement | Evidence | Result |
|---|---|---|
| Benchmark formulas | `test_benchmark_metrics_follow_contract_formulas` + committed `bench.json` | Pass |
| Soak stability | `test_soak_is_deterministic_and_reports_no_crashes` + `soak.json` | Pass |
| Leaderboard top 10 / export | `test_leaderboard_validates_sorts_and_keeps_top_ten` | Pass |
| Contract v1.3 commands | `game.contract.json` `bench_cmd` / `soak_cmd` | Present |
| Phase 1–3 regression | full `unittest discover` | Pass |

`peak_mem_mb` in `bench.json` is `null` because the measured scene runs inside a browser page; process RSS for the harness is not the same as the WebGL page heap. Soak still reports process RSS for leak detection.
