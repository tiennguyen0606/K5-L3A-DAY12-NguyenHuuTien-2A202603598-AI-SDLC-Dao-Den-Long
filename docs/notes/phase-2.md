# Phase 2 — Ticket-02: Ba hòn đảo

## Acceptance criteria

- Standard tuning: run 6 m/s, dash 14 m/s for 0.2 s with 1.5 s cooldown, carry 10, lantern cost 10, pulse 3/5 m/3 s.
- Nights 1/2/3 expose 5/6/7 standard lanterns and last 300/330/360 seconds.
- Dash is edge-triggered; Charm lasts 600 ticks, changes run speed to 7.2 m/s, and removes dash cooldown.
- Pause advances outer `tick`, while `sim_tick`, time, cooldowns, TTL and spawning remain frozen.
- Drifter steals up to three motes once; pulse during flee drops its stolen motes.
- Scenario can replace shades, drifters and charms and set v1.1 player counters.
- Snapshot contains all mandatory v1.1 collections and player fields; Phase 1 scenarios remain valid.

## Design change

Phase 1 renderer/core separation was retained. The simulation now owns three map layouts and all v1.1 entities. New state is expressed as deterministic integer tick counters; seconds are only derived at snapshot time. This avoids floating point drift and makes pause semantics explicit.

## AI log and evaluation

- Used Codex with a red/green loop: six Phase 2 tests failed against the Phase 1 tag, then passed after the smallest compatible extensions.
- Estimated Phase 2 usage: about 22k tokens. Savings came from extending the data-oriented core instead of adding an engine or dependencies.
- Phase 1 regression: 6/6 tests remain green; total suite is 15 tests.
- Known limitation: browser presentation is intentionally lightweight; audio/settings polish and detailed multi-level collision are not as complete as the contract simulation.

