# Phase 4 proof

Tags: `phase-4` (`0b25828`), Release `v1.0.0` (`05d787b` and later main)

```bash
python -m unittest tests/test_phase4.py -v
python scripts/verify.py
python -m lantern_islands.benchmark --seed 42 --duration 30 --out bench.json
python -m lantern_islands.soak --seed 7 --nights 10 --out soak.json
```

| Requirement | Evidence | Result |
|---|---|---|
| Benchmark formulas | `test_benchmark_metrics_follow_contract_formulas` | Pass |
| Live bench output | committed `bench.json` (`avg_fps` ≥ 60) | Pass on author machine |
| Soak stability | committed `soak.json` (`crashes: 0`) | Pass |
| Leaderboard | `test_leaderboard_validates_sorts_and_keeps_top_ten` | Pass |
| CI automation | `.github/workflows/ci.yml` | Present |
| Agent verify gate | `scripts/verify.py` + `AGENTS.md` | Present |
| Demo | `docs/demo/` (+ `demo.mp4` when available) | Screenshots committed |

`peak_mem_mb` is `null` because the measured scene runs in a browser page; soak reports process RSS for leak detection instead.

Machine note for author `bench.json`: Windows 10, Chrome headless via CDP, 1280×720, vsync off flag.
