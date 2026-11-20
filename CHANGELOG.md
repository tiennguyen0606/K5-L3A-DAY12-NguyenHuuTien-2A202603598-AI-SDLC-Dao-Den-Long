# Changelog

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

