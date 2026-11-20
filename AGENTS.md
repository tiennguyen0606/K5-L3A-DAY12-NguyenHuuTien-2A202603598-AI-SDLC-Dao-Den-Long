# Agent guide

- Runtime: Python 3.11+ standard library; browser client is dependency-free HTML/CSS/JS.
- Run all checks: `python3 -m unittest discover -s tests -v`.
- Headless smoke test: `python3 -m lantern_islands --seed 1 --night 1 --ticks 60 --out run.jsonl`.
- Keep gameplay rules in `lantern_islands/`; rendering must not affect deterministic state.
- Add a failing test before changing behavior. Never weaken or skip a red test.
- JSONL events use the resulting tick; snapshot tick 0 precedes input.
- Do not edit generated evidence. Regenerate it with commands documented under `docs/proof/`.

