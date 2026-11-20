# Phase 4 — Bình minh v1.0.0

## Acceptance criteria

- Benchmark scene matches Ticket-04 (200 shades, 100 motes, L1–L3 lit) and writes `bench.json` with contract formulas.
- Soak runs 10 nights in one process with `crashes = 0` and `mem_end_mb ≤ 1.2 × mem_start_mb`.
- Leaderboard validates names, keeps top 10, persists locally, exports ordered JSON.
- Accessibility covers remappable actions, volume, sensitivity, reduced motion, large UI, and visual warnings.
- README documents install/play/test/bench/soak within the lab constraints; CHANGELOG covers all four phases.

## Evaluation

- Bench initially sat at ~59.8 FPS; reducing shadows/antialias/geometry lifted it just over 60.
- Estimated Phase 4 polish/release usage: ~20k tokens.
