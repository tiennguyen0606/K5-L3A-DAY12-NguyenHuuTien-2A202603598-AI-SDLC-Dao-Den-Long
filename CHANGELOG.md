# Changelog

## Phase 4 — Contract v1.3 / v1.0.0

### Added

- `bench_cmd` / `soak_cmd` in `game.contract.json`, plus `bench.json` and `soak.json` evidence.
- Local leaderboard (top 10, export via `--export-leaderboard`).
- Accessibility: remappable keys, volume, mouse sensitivity, reduced motion, large UI, visual banners for shade spawn, wind, countdown, and low fuel.
- Release packaging docs, retro, and demo notes under `docs/`.
- GitHub Actions CI (`.github/workflows/ci.yml`) and `scripts/verify.py` agent gate.
- `docs/demo/demo.mp4` gameplay/evidence clip; remote tags `phase-1`…`phase-4`.

## Phase 3 — Contract v1.2

### Breaking changes

- Victory no longer occurs when every lantern is lit; the night runs until dawn.
- Night durations changed from 300/330/360 to 240/270/300 seconds.
- Lanterns consume fuel, can go out, can be refuelled, and cost five motes to relight.
- Low-fuel lanterns lose their safe zone and can be drained by wandering Shades.
- Scoring now awards 5 per deposited/refuel mote, 100 first light, 40 relight, and dawn bonuses; the time bonus was removed.
- Carry capacity now grows by two for every successful lighting, capped at 20.
- JSON contract is v1.2; snapshots, scenarios and events include the new fuel state.

### Added

- Distinguishable color accessibility setting for danger and Shade outlines.
- `refuel`, `lantern_out`, and `fuel_drain` events.
- ADR documenting the state-model and dawn-outcome migration.

## Phase 2 — Contract v1.1

### Added

- Three nights with standardized maps, dash, pause, charms, drifters, wind on Night 3.
- Snapshot fields for velocity, cooldowns, motes/drifters/charms collections.
- Acceptance criteria and proof under `docs/notes/phase-2.md` and `docs/proof/phase-2.md`.

### Changed

- Tuning locked to the Ticket-02 table; Phase 1 free values replaced.

## Phase 1 — Contract v1.0

### Added

- Deterministic headless core, JSONL contract output, browser playable Night 1 loop.
- `game.contract.json`, `AGENTS.md`, assumptions and proof notes.
