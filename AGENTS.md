# Agent guide

- Runtime: Python 3.11+ standard library; browser client is dependency-free HTML/CSS/JS.
- Run all checks: `python3 -m unittest discover -s tests -v`.
- Verify browser input math: `node --test tests/test_web_controls.mjs`.
- Headless smoke test: `python3 -m lantern_islands --seed 1 --night 2 --ticks 1200 --out run.jsonl`.
- Benchmark: `python3 -m lantern_islands.benchmark --seed 42 --duration 30 --out bench.json` (needs Chrome).
- Soak: `python3 -m lantern_islands.soak --seed 7 --nights 10 --out soak.json`.
- Playable server: `python3 -m lantern_islands.webapp`.
- Keep gameplay rules in `lantern_islands/`; rendering must not affect deterministic state.
- Creative entities/effects must stay off (or inert) in headless, benchmark, and soak paths.
- Add a failing test before changing behavior. Never weaken or skip a red test.
- JSONL events use the resulting tick; snapshot tick 0 precedes input.
- Contract v1.3 keeps v1.2 tick order. Pause advances `tick` only; all gameplay timers use `sim_tick`.
- Store lantern fuel as integer sixtieths (`fuel_units`) and round only in snapshots/events.
- Winning is evaluated only at dawn; never restore the removed `all_lit` early win.
- Phase 1–3 regression tests must remain green for every Phase 4 change.
- Do not edit generated evidence (`bench.json`, `soak.json`). Regenerate with the commands above and docs under `docs/proof/`.
