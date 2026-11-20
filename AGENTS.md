# Agent guide

- Runtime: Python 3.11+ standard library; browser client is dependency-free HTML/CSS/JS.
- Run all checks: `python3 -m unittest discover -s tests -v`.
- Headless smoke test: `python3 -m lantern_islands --seed 1 --night 2 --ticks 1200 --out run.jsonl`.
- Keep gameplay rules in `lantern_islands/`; rendering must not affect deterministic state.
- Add a failing test before changing behavior. Never weaken or skip a red test.
- JSONL events use the resulting tick; snapshot tick 0 precedes input.
- Contract v1.2 tick order is authoritative. Pause advances `tick` only; all gameplay timers use `sim_tick`.
- Store lantern fuel as integer sixtieths (`fuel_units`) and round only in snapshots/events.
- Winning is evaluated only at dawn; never restore the removed `all_lit` early win.
- Phase 1 regression tests must remain green for every Phase 2 change.
- Do not edit generated evidence. Regenerate it with commands documented under `docs/proof/`.

