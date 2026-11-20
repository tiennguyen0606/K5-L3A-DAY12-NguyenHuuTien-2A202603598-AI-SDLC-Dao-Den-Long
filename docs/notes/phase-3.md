# Phase 3 — Đèn cạn dầu

## Acceptance criteria and verification

- Fuel uses deterministic integer sixtieths and decays at exactly 1 unit/second.
- Interaction selects the nearest receivable lantern: an unlit lantern or a lit lantern below full fuel.
- First light costs 10; relight costs 5; refuel converts one mote into 10 fuel.
- Wander Shades select weak lanterns, enter `drain` within 2 m, and emit `fuel_drain` every 60 drain ticks.
- The game never wins early. At dawn it needs 3/5, 4/6, or 5/7 lit lanterns.
- **Night durations replace Ticket-02:** 240 / 270 / 300 seconds (was 300 / 330 / 360). Documented in `CHANGELOG.md` Phase 3 breaking changes and `docs/adr/0001-lantern-fuel-and-dawn.md`.
- Capacity is `min(20, 10 + 2 × successful_lights)`.
- Snapshot v1.2 contains fuel, `ever_lit`, `relit_count`, and capacity.

## AI evaluation

- Six Phase 3 tests were written red before implementation.
- Two old assertions failed because Phase 3 explicitly replaced scoring and durations (including the night-length table); both were updated with reasons rather than skipped.
- Estimated usage: 14k tokens for requirements, tests, implementation and review.

